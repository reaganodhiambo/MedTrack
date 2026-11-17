from datetime import date

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import localdate

from .models import (
    Medication,
    MedicationAdministration,
    MedicationSchedule,
    Patient,
)


class MedicationRoundsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="nurse-reagan", password="safe-test-password")
        self.client.force_login(self.user)
        self.patient = Patient.objects.create(
            first_name="Avery",
            last_name="Patient",
            date_of_birth=date(1950, 4, 12),
            gender="Female",
        )
        self.medication = Medication.objects.create(
            patient=self.patient,
            name="Vitamin D",
            dose="1000 IU",
            how_often="Once daily",
            start_date=localdate(),
        )
        MedicationSchedule.objects.create(
            medication=self.medication,
            slot=MedicationSchedule.Slot.MORNING,
        )

    def test_dashboard_shows_patient_medication_and_pending_round(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Avery Patient")
        self.assertContains(response, "Vitamin D")
        self.assertContains(response, "Mark given")

    def test_dose_can_be_marked_once_only(self):
        dose_url = reverse(
            "administer_dose",
            args=[self.medication.pk, MedicationSchedule.Slot.MORNING],
        )
        data = {"date": localdate().isoformat()}

        first_response = self.client.post(dose_url, data)
        second_response = self.client.post(dose_url, data)

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(MedicationAdministration.objects.count(), 1)
        administration = MedicationAdministration.objects.get()
        self.assertEqual(administration.administered_by, "nurse-lee")
        self.assertContains(
            self.client.get(f"/?date={localdate().isoformat()}"), "Given"
        )

    def test_dose_cannot_be_recorded_for_an_unscheduled_slot(self):
        response = self.client.post(
            reverse(
                "administer_dose",
                args=[self.medication.pk, MedicationSchedule.Slot.EVENING],
            ),
            {"date": localdate().isoformat()},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(MedicationAdministration.objects.exists())

    def test_patient_records_require_staff_sign_in(self):
        self.client.logout()

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('dashboard')}"
        )
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_database_rejects_duplicate_schedule_and_administration(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            MedicationSchedule.objects.create(
                medication=self.medication,
                slot=MedicationSchedule.Slot.MORNING,
            )

        MedicationAdministration.objects.create(
            medication=self.medication,
            date=localdate(),
            slot=MedicationSchedule.Slot.MORNING,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            MedicationAdministration.objects.create(
                medication=self.medication,
                date=localdate(),
                slot=MedicationSchedule.Slot.MORNING,
            )

    def test_medication_form_creates_multiple_slots(self):
        response = self.client.post(
            reverse("medication_create"),
            {
                "patient": self.patient.pk,
                "name": "Pain relief",
                "dose": "1 tablet",
                "how_often": "Daily",
                "start_date": localdate().isoformat(),
                "end_date": "",
                "slots": ["morning", "evening"],
                "morning_time": "08:00",
                "evening_time": "20:00",
            },
        )

        self.assertEqual(response.status_code, 302)
        medication = Medication.objects.get(name="Pain relief")
        self.assertEqual(
            list(medication.schedules.order_by("slot").values_list("slot", flat=True)),
            ["evening", "morning"],
        )
        self.assertEqual(
            medication.schedules.get(slot="morning").scheduled_time.isoformat(),
            "08:00:00",
        )

    def test_patient_table_links_to_detail_page(self):
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, reverse("patient_detail", args=[self.patient.pk]))
        self.assertContains(response, "View")

    def test_patient_detail_can_add_medication_for_that_patient(self):
        response = self.client.post(
            reverse("patient_medication_create", args=[self.patient.pk]),
            {
                "patient": self.patient.pk,
                "name": "Evening medicine",
                "dose": "5 mg",
                "how_often": "Once daily",
                "start_date": localdate().isoformat(),
                "end_date": "",
                "slots": ["evening"],
                "evening_time": "20:00",
            },
        )

        self.assertRedirects(
            response, reverse("patient_detail", args=[self.patient.pk])
        )
        medication = Medication.objects.get(name="Evening medicine")
        self.assertEqual(medication.patient, self.patient)

    def test_patient_detail_displays_assigned_medications_and_add_action(self):
        response = self.client.get(
            reverse("patient_detail", args=[self.patient.pk])
        )

        self.assertContains(response, "Vitamin D")
        self.assertContains(
            response,
            reverse("patient_medication_create", args=[self.patient.pk]),
        )

    def test_patient_medication_form_renders(self):
        response = self.client.get(
            reverse("patient_medication_create", args=[self.patient.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How often")
        self.assertContains(response, "Daily schedule")
