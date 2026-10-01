from django.contrib import admin
from .models import UserProfile, Patient, Vaccine, VaccineInventory, VaccinationRecord, Appointment, Recommendation
from django.utils.html import format_html
from django.utils import timezone
from .models import Notification


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
    list_display = ['user', 'user_type', 'phone_number', 'city', 'state', 'is_verified', 'created_at']
    list_filter = ['user_type', 'city', 'state', 'is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number', 'license_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_type', 'profile_image')
        }),
        ('Personal Information', {
            'fields': ('phone_number', 'date_of_birth', 'address', 'city', 'state', 'zip_code')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Professional Information', {
            'fields': ('license_number', 'specialization', 'years_of_experience')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'date_of_birth', 'age', 'gender', 'blood_type', 'created_at']
    list_filter = ['gender', 'blood_type', 'created_at']
    search_fields = ['first_name', 'last_name', 'patient_email', 'medical_record_number']
    readonly_fields = ['age', 'full_name', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'first_name', 'last_name', 'date_of_birth', 'gender', 'profile_image')
        }),
        ('Contact Information', {
            'fields': ('patient_phone', 'patient_email')
        }),
        ('Medical Information', {
            'fields': ('blood_type', 'weight', 'height', 'allergies', 'medical_conditions', 'current_medications')
        }),
        ('Additional Information', {
            'fields': ('relationship_to_guardian', 'medical_record_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

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
        ('Tracking', {
            'fields': ('received_date', 'received_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
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
        'reaction',
        'certificate_issued'
    ]
    
    list_filter = [
        'status', 
        'reaction', 
        'vaccine__name', 
        'date_administered',
        'follow_up_required',
        'certificate_issued'
    ]
    
    search_fields = [
        'patient__first_name', 
        'patient__last_name', 
        'vaccine__name',
        'lot_number',
        'certificate_number'
    ]
    
    readonly_fields = [
        'is_complete', 
        'is_overdue',
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'date_administered'
    
    fieldsets = (
        ('Patient & Vaccine', {
            'fields': ('patient', 'vaccine', 'inventory_used')
        }),
        ('Dose Information', {
            'fields': ('dose_number', 'total_doses')
        }),
        ('Administration Details', {
            'fields': ('date_administered', 'next_due_date', 'administered_by', 'administering_facility')
        }),
        ('Batch Information', {
            'fields': ('lot_number', 'expiration_date')
        }),
        ('Status & Reactions', {
            'fields': ('status', 'reaction', 'reaction_notes')
        }),
        ('Follow-up', {
            'fields': ('follow_up_required', 'follow_up_date', 'notes')
        }),
        ('Certificate', {
            'fields': ('certificate_number', 'certificate_issued', 'certificate_issued_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 
        'appointment_type', 
        'scheduled_date', 
        'status',
        'get_assigned_staff'
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
        'assigned_doctor__username',
        'assigned_nurse__username',
        'reason'
    ]
    
    readonly_fields = [
        'is_upcoming', 
        'is_past_due',
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'appointment_type', 'vaccine', 'is_vaccination')
        }),
        ('Schedule', {
            'fields': ('scheduled_date', 'duration', 'status')
        }),
        ('Staff Assignment', {
            'fields': ('assigned_doctor', 'assigned_nurse')
        }),
        ('Details', {
            'fields': ('reason', 'symptoms', 'notes')
        }),
        ('Reminders', {
            'fields': ('reminder_sent', 'follow_up_required')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_assigned_staff(self, obj):
        return obj.get_assigned_staff_display()
    get_assigned_staff.short_description = 'Assigned Staff'


# =============================================
# RECOMMENDATION MODEL ADMIN REGISTRATION
# =============================================

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """
    Admin interface for the Recommendation model
    """
    list_display = [
        'title', 
        'recommendation_type', 
        'priority', 
        'status', 
        'get_priority_colored',
        'get_status_colored',
        'created_at',
        'days_since_created'
    ]
    
    list_filter = [
        'status', 
        'priority', 
        'recommendation_type',
        'is_automated',
        'created_at'
    ]
    
    search_fields = [
        'title', 
        'description', 
        'justification',
        'trigger_reason'
    ]
    
    readonly_fields = [
        'created_at', 
        'updated_at',
        'days_since_created',
        'is_overdue'
    ]
    
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 
                'description', 
                'recommendation_type', 
                'priority', 
                'status'
            )
        }),
        ('Related Items', {
            'fields': (
                'vaccine', 
                'vaccine_inventory', 
                'created_by', 
                'reviewed_by'
            )
        }),
        ('Quantity & Cost', {
            'fields': (
                'recommended_quantity', 
                'current_stock', 
                'estimated_cost'
            )
        }),
        ('Timing', {
            'fields': (
                'suggested_date', 
                'expiry_alert_date'
            )
        }),
        ('Justification', {
            'fields': (
                'justification', 
                'benefits', 
                'risks', 
                'implementation_notes'
            )
        }),
        ('Review Information', {
            'fields': (
                'review_notes', 
                'review_date'
            )
        }),
        ('Attachments & Links', {
            'fields': (
                'attachment', 
                'reference_link'
            )
        }),
        ('Automation', {
            'fields': (
                'is_automated', 
                'trigger_reason'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at'
            )
        }),
    )
    
    actions = ['approve_recommendations', 'reject_recommendations', 'mark_as_implemented']
    
    def get_priority_colored(self, obj):
        """
        Display priority with colored badges
        """
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark',
        }
        color = colors.get(obj.priority, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_priority_display()
        )
    get_priority_colored.short_description = 'Priority'
    get_priority_colored.admin_order_field = 'priority'
    
    def get_status_colored(self, obj):
        """
        Display status with colored badges
        """
        colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'implemented': 'info',
            'archived': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'
    get_status_colored.admin_order_field = 'status'
    
    def days_since_created(self, obj):
        """
        Display days since recommendation was created
        """
        days = obj.days_since_created()
        if days == 0:
            return 'Today'
        elif days == 1:
            return 'Yesterday'
        else:
            return f'{days} days ago'
    days_since_created.short_description = 'Age'
    days_since_created.admin_order_field = 'created_at'
    
    def approve_recommendations(self, request, queryset):
        """
        Bulk action to approve selected recommendations
        """
        updated = queryset.update(
            status='approved',
            reviewed_by=request.user,
            review_date=timezone.now()
        )
        self.message_user(request, f'{updated} recommendation(s) approved successfully.')
    approve_recommendations.short_description = "Approve selected recommendations"
    
    def reject_recommendations(self, request, queryset):
        """
        Bulk action to reject selected recommendations
        """
        updated = queryset.update(
            status='rejected',
            reviewed_by=request.user,
            review_date=timezone.now()
        )
        self.message_user(request, f'{updated} recommendation(s) rejected.')
    reject_recommendations.short_description = "Reject selected recommendations"
    
    def mark_as_implemented(self, request, queryset):
        """
        Bulk action to mark recommendations as implemented
        """
        updated = queryset.update(status='implemented')
        self.message_user(request, f'{updated} recommendation(s) marked as implemented.')
    mark_as_implemented.short_description = "Mark as implemented"
    
    def save_model(self, request, obj, form, change):
        """
        Auto-set created_by when creating new recommendation
        """
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Optional: Customize admin site header and title
admin.site.site_header = "HealthCoach Vaccine Management System"
admin.site.site_title = "HealthCoach Admin"
admin.site.index_title = "Vaccine Management Administration"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'is_sent', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_sent', 'created_at']
    search_fields = ['title', 'message', 'recipient__username']
    readonly_fields = ['created_at', 'sent_at']
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('title', 'message', 'notification_type')
        }),
        ('Recipient', {
            'fields': ('recipient', 'is_for_all')
        }),
        ('Related Objects', {
            'fields': ('schedule',)
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'sent_at')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at')
        }),
    )
# =============================================
# VAXGUARD ADMIN REGISTRATIONS
# =============================================
from .models import (
    Symptom,
    MonitoringSession,
    SensorReading,
    SymptomReport,
    RiskAssessment,
    Alert,
    ClinicalResponse,
    Outcome,
)


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity_level', 'is_active', 'created_at']
    list_filter = ['severity_level', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['severity_level', 'name']


@admin.register(MonitoringSession)
class MonitoringSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'patient', 'vaccination_record', 'start_time',
        'planned_duration_minutes', 'current_level', 'status', 'started_by'
    ]
    list_filter = ['status', 'current_level', 'start_time']
    search_fields = ['patient__first_name', 'patient__last_name']
    readonly_fields = ['created_at', 'updated_at', 'elapsed_minutes']
    date_hierarchy = 'start_time'

    fieldsets = (
        ('Core', {
            'fields': ('vaccination_record', 'patient', 'started_by')
        }),
        ('Timing', {
            'fields': ('start_time', 'planned_duration_minutes', 'end_time')
        }),
        ('Status', {
            'fields': ('status', 'current_level')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'elapsed_minutes')
        }),
    )


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'device_id', 'heart_rate',
        'spo2', 'temperature', 'recorded_at'
    ]
    list_filter = ['device_id', 'recorded_at']
    search_fields = ['device_id', 'session__id']
    date_hierarchy = 'recorded_at'


@admin.register(SymptomReport)
class SymptomReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'symptom', 'reported_by_type',
        'reported_by', 'reported_at'
    ]
    list_filter = ['reported_by_type', 'reported_at']
    search_fields = ['symptom__name', 'session__id']
    date_hierarchy = 'reported_at'


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'level', 'assessed_at']
    list_filter = ['level', 'assessed_at']
    search_fields = ['session__id', 'reason']
    date_hierarchy = 'assessed_at'
    readonly_fields = ['assessed_at']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'level', 'status',
        'created_at', 'acknowledged_at', 'acknowledged_by'
    ]
    list_filter = ['level', 'status', 'created_at']
    search_fields = ['session__id', 'reason']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'acknowledgement_seconds']

    fieldsets = (
        ('Core', {
            'fields': ('session', 'level', 'status')
        }),
        ('Trigger', {
            'fields': ('reason', 'risk_assessment')
        }),
        ('Timeline', {
            'fields': ('created_at', 'acknowledged_at', 'acknowledged_by', 'resolved_at')
        }),
    )


@admin.register(ClinicalResponse)
class ClinicalResponseAdmin(admin.ModelAdmin):
    list_display = ['id', 'alert', 'responded_by', 'responded_at', 'referral_facility']
    list_filter = ['responded_at']
    search_fields = ['alert__id', 'assessment_notes', 'action_taken']
    date_hierarchy = 'responded_at'


@admin.register(Outcome)
class OutcomeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'outcome_type', 'follow_up_date',
        'recorded_by', 'recorded_at'
    ]
    list_filter = ['outcome_type', 'recorded_at']
    search_fields = ['session__id', 'notes']
    date_hierarchy = 'recorded_at'