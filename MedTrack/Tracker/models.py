from django.db import models


class Patient(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Medication(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medications"
    )
    name = models.CharField(max_length=100)
    dose = models.CharField(max_length=50)
    how_often = models.CharField(max_length=50, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — {self.patient}"


class MedicationSchedule(models.Model):
    class Slot(models.TextChoices):
        MORNING = "morning", "Morning"
        AFTERNOON = "afternoon", "Afternoon"
        EVENING = "evening", "Evening"

    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name="schedules"
    )
    slot = models.CharField(max_length=10, choices=Slot.choices)
    scheduled_time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ["slot", "scheduled_time", "medication__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["medication", "slot"],
                name="unique_medication_schedule_slot",
            )
        ]

    def __str__(self):
        return f"{self.medication.name} — {self.get_slot_display()}"


class MedicationAdministration(models.Model):
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name="administrations"
    )
    date = models.DateField()
    slot = models.CharField(max_length=10, choices=MedicationSchedule.Slot.choices)
    administered_at = models.DateTimeField(auto_now_add=True)
    administered_by = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ["-administered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["medication", "date", "slot"],
                name="unique_medication_administration_per_slot",
            )
        ]

    def __str__(self):
        return f"{self.medication.name} — {self.date} ({self.slot})"
