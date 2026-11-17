from django.contrib import admin

from .models import Medication, MedicationAdministration, MedicationSchedule, Patient


class MedicationScheduleInline(admin.TabularInline):
    model = MedicationSchedule
    extra = 1


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "date_of_birth", "gender")
    search_fields = ("first_name", "last_name")


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "patient", "dose", "how_often", "start_date", "end_date")
    list_filter = ("start_date", "end_date")
    search_fields = ("name", "patient__first_name", "patient__last_name")
    inlines = [MedicationScheduleInline]


@admin.register(MedicationAdministration)
class MedicationAdministrationAdmin(admin.ModelAdmin):
    list_display = ("medication", "date", "slot", "administered_at", "administered_by")
    list_filter = ("date", "slot")
    search_fields = ("medication__name", "administered_by")
