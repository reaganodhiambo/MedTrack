from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.timezone import localdate
from django.views.decorators.http import require_POST

from .forms import MedicationForm, PatientForm
from .models import (
    Medication,
    MedicationAdministration,
    MedicationSchedule,
    Patient,
)


@login_required
def dashboard(request):
    selected_date = localdate()
    date_value = request.GET.get("date")
    if date_value:
        parsed_date = parse_date(date_value)
        if parsed_date is None:
            messages.error(request, "Choose a valid date.")
        else:
            selected_date = parsed_date

    doses = MedicationAdministration.objects.filter(date=selected_date)
    dose_by_medication_and_slot = {
        (dose.medication_id, dose.slot): dose for dose in doses
    }
    slots = []
    for slot, title in MedicationSchedule.Slot.choices:
        entries = []
        schedules = (
            MedicationSchedule.objects.filter(slot=slot)
            .select_related("medication", "medication__patient")
            .order_by("medication__patient__last_name", "medication__name")
        )
        for schedule in schedules:
            medication = schedule.medication
            if medication.start_date > selected_date or (
                medication.end_date and medication.end_date < selected_date
            ):
                continue
            entries.append(
                {
                    "schedule": schedule,
                    "medication": medication,
                    "patient": medication.patient,
                    "administration": dose_by_medication_and_slot.get(
                        (medication.id, slot)
                    ),
                }
            )
        slots.append({"key": slot, "title": title, "entries": entries})

    patients = Patient.objects.prefetch_related("medications__schedules")
    return render(
        request,
        "Tracker/dashboard.html",
        {
            "patients": patients,
            "slots": slots,
            "selected_date": selected_date,
            "scheduled_count": sum(len(slot["entries"]) for slot in slots),
            "administered_count": sum(
                entry["administration"] is not None
                for slot in slots
                for entry in slot["entries"]
            ),
        },
    )


@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(
        Patient.objects.prefetch_related("medications__schedules"), pk=patient_id
    )
    selected_date = localdate()
    date_value = request.GET.get("date")
    if date_value:
        parsed_date = parse_date(date_value)
        if parsed_date is None:
            messages.error(request, "Choose a valid date.")
        else:
            selected_date = parsed_date

    administrations = MedicationAdministration.objects.filter(
        medication__patient=patient, date=selected_date
    )
    administered = {
        (dose.medication_id, dose.slot): dose for dose in administrations
    }
    rounds = []
    for slot, title in MedicationSchedule.Slot.choices:
        entries = []
        for schedule in (
            MedicationSchedule.objects.filter(medication__patient=patient, slot=slot)
            .select_related("medication")
        ):
            medication = schedule.medication
            if medication.start_date > selected_date or (
                medication.end_date and medication.end_date < selected_date
            ):
                continue
            entries.append(
                {
                    "schedule": schedule,
                    "medication": medication,
                    "administration": administered.get((medication.pk, slot)),
                }
            )
        rounds.append({"key": slot, "title": title, "entries": entries})

    return render(
        request,
        "Tracker/patient_detail.html",
        {
            "patient": patient,
            "rounds": rounds,
            "selected_date": selected_date,
            "active_medications": sum(
                medication.start_date <= selected_date
                and (medication.end_date is None or medication.end_date >= selected_date)
                for medication in patient.medications.all()
            ),
        },
    )


@login_required
def patient_create(request):
    form = PatientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        patient = form.save()
        messages.success(request, f"{patient} was added.")
        return redirect("dashboard")
    return render(request, "Tracker/patient_form.html", {"form": form})


@login_required
def medication_create(request):
    form = MedicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            medication = form.save()
            form.save_schedules(medication)
        messages.success(request, f"{medication.name} was added to the schedule.")
        return redirect("dashboard")
    return render(request, "Tracker/medication_form.html", {"form": form})


@login_required
def patient_medication_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    form = MedicationForm(request.POST or None, patient=patient)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            medication = form.save()
            form.save_schedules(medication)
        messages.success(request, f"{medication.name} was added to {patient}'s plan.")
        return redirect("patient_detail", patient_id=patient.pk)
    return render(
        request,
        "Tracker/medication_form.html",
        {"form": form, "patient": patient},
    )


@require_POST
@login_required
def administer_dose(request, medication_id, slot):
    if slot not in MedicationSchedule.Slot.values:
        messages.error(request, "That medication time slot is not valid.")
        return redirect("dashboard")

    medication = get_object_or_404(Medication, pk=medication_id)
    dose_date = parse_date(request.POST.get("date", ""))
    if dose_date is None:
        messages.error(request, "Choose a valid date before recording a dose.")
        return redirect("dashboard")
    if dose_date > localdate():
        messages.error(request, "A dose cannot be recorded before its scheduled date.")
        return redirect("dashboard")
    if not medication.schedules.filter(slot=slot).exists():
        messages.error(request, "This medication is not scheduled for that time slot.")
        return redirect(f"/?date={dose_date.isoformat()}")
    if medication.start_date > dose_date or (
        medication.end_date and medication.end_date < dose_date
    ):
        messages.error(request, "This medication is not active on the selected date.")
        return redirect(f"/?date={dose_date.isoformat()}")

    _, created = MedicationAdministration.objects.get_or_create(
        medication=medication,
        date=dose_date,
        slot=slot,
        defaults={"administered_by": request.user.get_username()},
    )

    if created:
        messages.success(request, f"{medication.name} marked as administered.")
    else:
        messages.warning(
            request, f"{medication.name} already has a recorded dose for this slot."
        )
    return redirect(f"/?date={dose_date.isoformat()}")
