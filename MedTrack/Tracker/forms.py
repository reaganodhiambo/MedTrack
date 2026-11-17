from django import forms

from .models import Medication, MedicationSchedule, Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["first_name", "last_name", "date_of_birth", "gender"]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "w-full rounded-md border border-slate-300 px-3 py-2 "
                "text-sm focus:border-teal-700 focus:outline-none"
            )


class MedicationForm(forms.ModelForm):
    slots = forms.MultipleChoiceField(
        choices=MedicationSchedule.Slot.choices,
        widget=forms.CheckboxSelectMultiple,
        label="Daily schedule",
    )
    morning_time = forms.TimeField(
        required=False, widget=forms.TimeInput(attrs={"type": "time"})
    )
    afternoon_time = forms.TimeField(
        required=False, widget=forms.TimeInput(attrs={"type": "time"})
    )
    evening_time = forms.TimeField(
        required=False, widget=forms.TimeInput(attrs={"type": "time"})
    )

    class Meta:
        model = Medication
        fields = [
            "patient",
            "name",
            "dose",
            "how_often",
            "start_date",
            "end_date",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, patient=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs["class"] = (
                    "w-full rounded-md border border-slate-300 px-3 py-2 "
                    "text-sm focus:border-teal-700 focus:outline-none"
                )
        if patient is not None:
            self.fields["patient"].queryset = Patient.objects.filter(pk=patient.pk)
            self.fields["patient"].initial = patient.pk
            self.fields["patient"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date must be on or after the start date.")
        return cleaned_data

    def save_schedules(self, medication):
        time_fields = {
            MedicationSchedule.Slot.MORNING: "morning_time",
            MedicationSchedule.Slot.AFTERNOON: "afternoon_time",
            MedicationSchedule.Slot.EVENING: "evening_time",
        }
        MedicationSchedule.objects.bulk_create(
            [
                MedicationSchedule(
                    medication=medication,
                    slot=slot,
                    scheduled_time=self.cleaned_data[time_fields[slot]],
                )
                for slot in self.cleaned_data["slots"]
            ]
        )
