from django.urls import path
from . import views
from .views import profile, view_vaccination_record, edit_vaccination_record, delete_vaccination_record
from .views import settings_dashboard, change_password, update_display_settings, change_language

urlpatterns = [
    # =============================================
    # YOUR EXISTING URLS - KEPT EXACTLY AS THEY WERE
    # =============================================
    
    # Main Pages
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('service/', views.service, name='service'),
    path('vaccine/', views.vaccine, name='vaccine'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/', profile, name='profile'),
    
    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # =============================================
    # VACCINE INVENTORY MANAGEMENT
    # =============================================
    path('vaccine-inventory/', views.vaccine_inventory, name='vaccine_inventory'),
    path('edit-vaccine-inventory/<int:inventory_id>/', views.edit_vaccine_inventory, name='edit_vaccine_inventory'),
    path('delete-vaccine-inventory/<int:inventory_id>/', views.delete_vaccine_inventory, name='delete_vaccine_inventory'),
    path('vaccine-details/<int:inventory_id>/', views.vaccine_details, name='vaccine_details'),
    
    # =============================================
    # VACCINE API ENDPOINTS
    # =============================================
    path('api/vaccines/<int:vaccine_id>/', views.vaccine_detail_api, name='vaccine_detail_api'),
    path('api/vaccines/<int:vaccine_id>/delete/', views.delete_vaccine_api, name='delete_vaccine_api'),
    path('api/vaccines/create/', views.create_vaccine_api, name='create_vaccine_api'),
    path('api/vaccines/<int:vaccine_id>/update/', views.update_vaccine_api, name='update_vaccine_api'),
    # Note: create-vaccine-api/ (with hyphen) is kept for backward compatibility
    path('create-vaccine-api/', views.create_vaccine_api, name='create_vaccine_api_alt'),
    
    # =============================================
    # AJAX ENDPOINTS FOR SIGNUP VALIDATION
    # =============================================
    path('ajax/check-username/', views.check_username_availability, name='check_username'),
    path('ajax/check-email/', views.check_email_availability, name='check_email'),
    
    # =============================================
    # PATIENT MANAGEMENT
    # =============================================
     path('monitoring/start/<int:vaccination_id>/', views.start_monitoring, name='start_monitoring'),
    path('monitoring/<int:session_id>/', views.monitoring_live, name='monitoring_live'),
    path('patients/', views.patient_list, name='patient_list'),
    path('vaccination-schedule/', views.vaccination_schedule, name='vaccination_schedule'),
    path('immunization-records/', views.immunization_records, name='immunization_records'),
    path('coverage-analytics/', views.coverage_analytics, name='coverage_analytics'),
    path('recommendation/create/', views.create_recommendation, name='create_recommendation'),
    path('api/recommendations/<int:recommendation_id>/update-status/', views.update_recommendation_status, name='update_recommendation_status'),
    path('recommendation/edit/<int:pk>/', views.edit_recommendation, name='edit_recommendation'),
    path('recommendation/create/', views.create_recommendation, name='create_recommendation'),
    path('recommendation/edit/<int:pk>/', views.edit_recommendation, name='edit_recommendation'),
    path('recommendation/delete/<int:pk>/', views.delete_recommendation, name='delete_recommendation'),
    path('api/recommendations/create/', views.create_recommendation_api, name='create_recommendation_api'),
    path('api/recommendations/<int:recommendation_id>/delete/', views.delete_recommendation_api, name='delete_recommendation_api'),
    path('api/recommendations/<int:recommendation_id>/update-status/', views.update_recommendation_status, name='update_recommendation_status'),
    
    # =============================================
    # YOUR COLLEAGUE'S UNIQUE URLS - ADDED BELOW
    # =============================================
    
    # Patient Dashboard URLs (unique)
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),
    path('patient/profile/update/', views.update_patient_profile, name='update_patient_profile'),
    
    # Appointments URLs (unique)
    path('patient/appointments/', views.appointments, name='appointments'),
    path('appointments/create/', views.create_appointment, name='create_appointment'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/update-status/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
    
    # Consultation URLs (unique)
    path('consultation/', views.consultation, name='consultation'),
    path('consultation/create/', views.create_consultation, name='create_consultation'),
    path('consultation/management/', views.consultation_management, name='consultation_management'),
    
    # Prescription URLs (unique)
    path('patient/prescriptions/', views.prescriptions, name='prescriptions'),
    path('prescriptions/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
    path('prescriptions/refill/<int:prescription_id>/', views.request_refill, name='request_refill'),
    path('prescriptions/create/', views.create_prescription, name='create_prescription'),
    path('prescriptions/management/', views.prescription_management, name='prescription_management'),
    
    # Medical Records URLs (unique)
    path('patient/medical-records/', views.medical_records, name='medical_records'),
    path('medical-records/create/', views.create_medical_record, name='create_medical_record'),
    path('medical-records/management/', views.medical_record_management, name='medical_record_management'),
    path('patient/download-medical-record/', views.download_medical_record, name='download_medical_record'),
    
    # Vaccination History URLs (unique)
    path('patient/vaccination-history/', views.vaccination_history, name='vaccination_history'),
    path('vaccination/schedule/', views.schedule_vaccination, name='schedule_vaccination'),
    path('vaccination/certificate/<int:record_id>/', views.download_vaccination_certificate, name='download_vaccination_certificate'),
    path('vaccination-records/create/', views.create_vaccination_record, name='create_vaccination_record'),
    path('vaccination-records/management/', views.vaccination_record_management, name='vaccination_record_management'),
    
    # VaxGuard: patient + vaccine status API
    path('api/patient-vaccine-status/<int:patient_id>/<int:vaccine_id>/',
         views.patient_vaccine_status_api,
         name='patient_vaccine_status_api'),

    # API URLs (unique)
    path('api/departments/', views.get_departments, name='get_departments'),
    path('api/doctors/', views.get_available_doctors, name='get_doctors'),
    path('api/available-slots/', views.get_available_slots, name='get_slots'),
    path('api/vaccines/', views.get_vaccines, name='get_vaccines'),
    path('patient/add/', views.add_patient, name='add_patient'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patient/edit/<int:patient_id>/', views.edit_patient, name='edit_patient'),
    path('patient/delete/<int:patient_id>/', views.delete_patient, name='delete_patient'),
    path('schedule-management/', views.vaccination_schedule_management, name='vaccination_schedule_management'),
    path('schedule/edit/<int:schedule_id>/', views.edit_vaccination_schedule, name='edit_vaccination_schedule'),
    path('schedule/delete/<int:schedule_id>/', views.delete_vaccination_schedule, name='delete_vaccination_schedule'),
    path('patient/schedules/', views.patient_vaccination_schedules, name='patient_schedules'),
    path('schedule/register/<int:schedule_id>/', views.register_for_schedule, name='register_for_schedule'),
    path('notifications/', views.my_notifications, name='my_notifications'),
    path('schedule/create/', views.create_vaccination_schedule, name='create_vaccination_schedule'),
    
    # Settings URLs
    path('settings/', settings_dashboard, name='settings'),
    path('settings/change-password/', change_password, name='change_password'),
    path('settings/display/', update_display_settings, name='display_settings'),
    path('settings/language/', change_language, name='change_language'),
    
    # =============================================
    # NOTIFICATION API ENDPOINTS - NEWLY ADDED
    # =============================================
    path('api/notifications/<int:notification_id>/', views.notification_detail_api, name='notification_detail_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/<int:notification_id>/delete/', views.delete_notification_api, name='delete_notification_api'),
    path('api/notifications/delete-all/', views.delete_all_notifications_api, name='delete_all_notifications_api'),
    path('notifications/edit/<int:notification_id>/', views.edit_notification, name='edit_notification'),
    path('vaccination-record/create/', views.create_vaccination_record, name='create_vaccination_record'),
    path('vaccination-record/<int:pk>/', view_vaccination_record, name='view_vaccination_record'),
    path('vaccination-record/<int:pk>/edit/', edit_vaccination_record, name='edit_vaccination_record'),
    path('vaccination-record/<int:pk>/delete/', delete_vaccination_record, name='delete_vaccination_record'),

]