from django.contrib import admin
from .models import UserProfile, Patient, Vaccine, VaccineInventory, VaccinationRecord, Appointment

@admin.register(Vaccine)
class VaccineAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'short_name', 
        'vaccine_type', 
        'manufacturer', 
        'doses_required',
        'is_active',
        'created_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'short_name', 
                'description',
                'vaccine_type',
                'target_diseases',
                'age_groups'  # Added this field
            )
        }),
        ('Dosage Information', {
            'fields': (
                'recommended_age',
                'doses_required',
                'days_between_doses'
            )
        }),
        ('Vaccine Details', {
            'fields': (
                'manufacturer',
                'storage_temperature', 
                'contraindications',
                'side_effects'
            )
        }),
        ('Administration', {
            'fields': (
                'route',
                'site'
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
            )
        }),
    )
    
    list_filter = [
        'vaccine_type',
        'is_active',
        'manufacturer',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'short_name',
        'manufacturer',
        'target_diseases'
    ]
    
    list_per_page = 25
    readonly_fields = ['created_at', 'updated_at']  # Added these
    date_hierarchy = 'created_at'  # Added date navigation

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'city', 'state', 'created_at']
    list_filter = ['city', 'state', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'date_of_birth', 'gender', 'blood_type', 'created_at']
    list_filter = ['gender', 'blood_type', 'created_at']
    search_fields = ['first_name', 'last_name', 'patient_email']
    readonly_fields = ['age', 'full_name', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

@admin.register(VaccineInventory)
class VaccineInventoryAdmin(admin.ModelAdmin):
    list_display = [
        'get_vaccine_name',  # Changed to use method for better display
        'lot_number', 
        'current_stock', 
        'min_stock_level', 
        'status', 
        'expiration_date',
        'is_expiring_soon'
    ]
    
    list_filter = [
        'status', 
        'vaccine__name', 
        'expiration_date',
        'vaccine_type',
        'created_at'
    ]
    
    search_fields = [
        'vaccine__name', 
        'vaccine_name',  # Added search for direct vaccine name
        'lot_number',
        'manufacturer'
    ]
    
    readonly_fields = [
        'status', 
        'is_expiring_soon', 
        'get_stock_percentage',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Vaccine Information', {
            'fields': (
                'vaccine',
                'vaccine_name',
                'vaccine_type',
                'manufacturer',
            )
        }),
        ('Stock Information', {
            'fields': (
                'current_stock',
                'min_stock_level',
                'doses_per_vial',
                'status',  # Read-only but good to show
            )
        }),
        ('Batch Information', {
            'fields': (
                'lot_number',
                'expiration_date',
            )
        }),
        ('Additional Information', {
            'fields': (
                'storage_temperature',
                'description',
                'target_diseases',
                'age_groups',
                'notes',
            )
        }),
    )
    
    def get_vaccine_name(self, obj):
        return obj.get_display_name()
    get_vaccine_name.short_description = 'Vaccine Name'
    get_vaccine_name.admin_order_field = 'vaccine__name'

@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 
        'vaccine', 
        'dose_number', 
        'total_doses',
        'date_administered', 
        'status', 
        'reaction'
    ]
    
    list_filter = [
        'status', 
        'reaction', 
        'vaccine__name', 
        'date_administered',
        'follow_up_required'
    ]
    
    search_fields = [
        'patient__first_name', 
        'patient__last_name', 
        'vaccine__name',
        'lot_number'
    ]
    
    readonly_fields = [
        'is_complete', 
        'is_overdue',
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'date_administered'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 
        'appointment_type', 
        'scheduled_date', 
        'status',
        'assigned_doctor'
    ]
    
    list_filter = [
        'appointment_type', 
        'status', 
        'scheduled_date',
        'is_vaccination'
    ]
    
    search_fields = [
        'patient__first_name', 
        'patient__last_name', 
        'assigned_doctor',
        'assigned_nurse'
    ]
    
    readonly_fields = [
        'is_upcoming', 
        'is_past_due',
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'scheduled_date'

# Optional: Customize admin site header and title
admin.site.site_header = "HealthCoach Vaccine Management System"
admin.site.site_title = "HealthCoach Admin"
admin.site.index_title = "Vaccine Management Administration"