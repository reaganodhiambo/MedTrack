from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("patients/add/", views.patient_create, name="patient_create"),
    path("patients/<int:patient_id>/", views.patient_detail, name="patient_detail"),
    path(
        "patients/<int:patient_id>/medications/add/",
        views.patient_medication_create,
        name="patient_medication_create",
    ),
    path("medications/add/", views.medication_create, name="medication_create"),
    path(
        "medications/<int:medication_id>/administer/<str:slot>/",
        views.administer_dose,
        name="administer_dose",
    ),
]