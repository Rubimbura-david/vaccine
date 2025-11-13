from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('service/', views.service, name='service'),
    path('vaccine/', views.vaccine, name='vaccine'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # VACCINE INVENTORY MANAGEMENT
    path('vaccine-inventory/', views.vaccine_inventory, name='vaccine_inventory'),
    path('edit-vaccine-inventory/<int:inventory_id>/', views.edit_vaccine_inventory, name='edit_vaccine_inventory'),
    path('delete-vaccine-inventory/<int:inventory_id>/', views.delete_vaccine_inventory, name='delete_vaccine_inventory'),
    path('vaccine-details/<int:inventory_id>/', views.vaccine_details, name='vaccine_details'),
    
    # VACCINE API ENDPOINTS
    path('api/vaccines/<int:vaccine_id>/', views.vaccine_detail_api, name='vaccine_detail_api'),
    path('api/vaccines/<int:vaccine_id>/delete/', views.delete_vaccine_api, name='delete_vaccine_api'),
    path('api/vaccines/create/', views.create_vaccine_api, name='create_vaccine_api'),
    path('api/vaccines/<int:vaccine_id>/update/', views.update_vaccine_api, name='update_vaccine_api'),
    
    # OTHER DASHBOARD URLS
    path('patients/', views.patient_list, name='patient_list'),
    path('vaccination-schedule/', views.vaccination_schedule, name='vaccination_schedule'),
    path('immunization-records/', views.immunization_records, name='immunization_records'),
    path('coverage-analytics/', views.coverage_analytics, name='coverage_analytics'),
    path('create-vaccine-api/', views.create_vaccine_api, name='create_vaccine_api'),
]