# models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, timedelta
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid

# =============================================
# YOUR EXISTING MODELS - KEPT EXACTLY AS THEY WERE
# =============================================


class UserProfile(models.Model):
    # ========== NEW USER TYPE FIELD ==========
    USER_TYPE_CHOICES = [
        ("patient", "🧑 Patient"),
        ("healthcare_worker", "👨‍⚕️ Healthcare Worker"),
        ("admin", "👑 Administrator"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # User Type/Role
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="patient",
        help_text="User role in the system - determines permissions and access levels",
    )

    # Personal Information
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)

    # Professional Information (for doctors/nurses)
    license_number = models.CharField(
        max_length=50, blank=True, null=True, help_text="Medical license number"
    )
    specialization = models.CharField(
        max_length=100, blank=True, null=True, help_text="Area of specialization"
    )
    years_of_experience = models.IntegerField(
        blank=True, null=True, help_text="Years of professional experience"
    )

    # Profile Image
    profile_image = models.ImageField(
        upload_to="profile_images/", blank=True, null=True
    )

    # Account Status
    is_verified = models.BooleanField(
        default=False, help_text="Whether the user's credentials have been verified"
    )
    verification_date = models.DateTimeField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.get_user_type_display()})"

    def age(self):
        if self.date_of_birth:
            today = date.today()
            return (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
        return None

    def is_healthcare_worker(self):
        """Check if user is a healthcare worker."""
        return self.user_type == "healthcare_worker"

    def is_admin(self):
        """Check if user is administrator."""
        return self.user_type == "admin"

    def is_patient(self):
        """Check if user is a patient."""
        return self.user_type == "patient"

    def get_display_name(self):
        """Get appropriate display name with title."""
        if self.user_type == "healthcare_worker":
            return f"HCW {self.user.get_full_name() or self.user.username}"
        elif self.user_type == "admin":
            return f"Admin {self.user.get_full_name() or self.user.username}"
        else:
            return self.user.get_full_name() or self.user.username


class Patient(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("U", "Unknown"),
    ]

    BLOOD_TYPE_CHOICES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
        ("UNK", "Unknown"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patients")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="U")
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, help_text="Weight in kg"
    )
    height = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, help_text="Height in cm"
    )

    # Medical Information
    blood_type = models.CharField(
        max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True, null=True
    )
    allergies = models.TextField(
        blank=True, null=True, help_text="List any known allergies"
    )
    medical_conditions = models.TextField(
        blank=True, null=True, help_text="List any medical conditions"
    )
    current_medications = models.TextField(
        blank=True, null=True, help_text="List current medications"
    )

    # Contact Information
    patient_phone = models.CharField(max_length=15, blank=True, null=True)
    patient_email = models.EmailField(blank=True, null=True)

    # Relationship to guardian (if patient is a child)
    relationship_to_guardian = models.CharField(
        max_length=50, blank=True, null=True, help_text="e.g., Son, Daughter, Ward"
    )

    # Medical IDs
    medical_record_number = models.CharField(
        max_length=50, blank=True, null=True, unique=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def age(self):
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def age_group(self):
        """Categorize patient into age group"""
        age = self.age()
        if age <= 1:
            return "infant"
        elif age <= 3:
            return "toddler"
        elif age <= 5:
            return "preschool"
        elif age <= 12:
            return "school_age"
        elif age <= 18:
            return "adolescent"
        else:
            return "adult"


class Vaccine(models.Model):
    VACCINE_TYPE_CHOICES = [
        ("combination", "Combination Vaccine"),
        ("single", "Single Antigen"),
        ("live", "Live Attenuated"),
        ("inactivated", "Inactivated"),
    ]

    AGE_GROUP_CHOICES = [
        ("infant", "Infant (0-12 months)"),
        ("toddler", "Toddler (1-3 years)"),
        ("preschool", "Preschool (3-5 years)"),
        ("school_age", "School Age (6-12 years)"),
        ("adolescent", "Adolescent (13-18 years)"),
    ]

    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    vaccine_type = models.CharField(
        max_length=20, choices=VACCINE_TYPE_CHOICES, default="single"
    )
    target_diseases = models.CharField(max_length=300, blank=True, null=True)

    # Recommended administration
    recommended_age = models.CharField(max_length=100, blank=True, null=True)
    doses_required = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    days_between_doses = models.IntegerField(
        blank=True, null=True, help_text="Days between doses"
    )

    # Age groups (from your form)
    age_groups = models.CharField(
        max_length=200, blank=True, null=True, help_text="Comma-separated age groups"
    )

    # Vaccine Information
    manufacturer = models.CharField(max_length=200, blank=True, null=True)
    storage_temperature = models.CharField(max_length=50, blank=True, null=True)
    contraindications = models.TextField(blank=True, null=True)
    side_effects = models.TextField(blank=True, null=True)

    # Administration
    route = models.CharField(
        max_length=50, blank=True, null=True, help_text="e.g., Intramuscular, Oral"
    )
    site = models.CharField(
        max_length=50, blank=True, null=True, help_text="e.g., Upper arm, Thigh"
    )

    cvx_code = models.CharField(
        max_length=10, blank=True, null=True, help_text="CVX vaccine code"
    )
    cdc_identifier = models.CharField(
        max_length=20, blank=True, null=True, help_text="CDC vaccine identifier"
    )

    # VaxGuard: default observation period after this vaccine is administered
    monitoring_duration_minutes = models.IntegerField(
        default=30, help_text="Default post-vaccination monitoring duration in minutes"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Vaccine"
        verbose_name_plural = "Vaccines"

    def __str__(self):
        return self.name

    def get_administered_count(self):
        """Get total number of times this vaccine has been administered"""
        return VaccinationRecord.objects.filter(
            vaccine=self, status="administered"
        ).count()

    def get_age_groups_list(self):
        """Return age groups as a list"""
        if self.age_groups:
            return self.age_groups.split(",")
        return []


class VaccineInventory(models.Model):
    STATUS_CHOICES = [
        ("in_stock", "In Stock"),
        ("low_stock", "Low Stock"),
        ("critical", "Critical"),
        ("out_of_stock", "Out of Stock"),
    ]

    # Basic Information (from your form)
    vaccine_name = models.CharField(
        max_length=200, blank=True, null=True
    )  # For direct entry without Vaccine FK
    vaccine = models.ForeignKey(
        Vaccine,
        on_delete=models.CASCADE,
        related_name="inventory",
        blank=True,
        null=True,
    )
    vaccine_type = models.CharField(
        max_length=20, choices=Vaccine.VACCINE_TYPE_CHOICES, blank=True, null=True
    )

    # Stock Information (from your form)
    current_stock = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    min_stock_level = models.IntegerField(validators=[MinValueValidator(1)], default=10)
    doses_per_vial = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    # Batch Information (from your form)
    lot_number = models.CharField(max_length=100)
    expiration_date = models.DateField()
    manufacturer = models.CharField(max_length=200, blank=True, null=True)

    # Storage Information (from your form)
    storage_temperature = models.CharField(max_length=50, blank=True, null=True)

    # Additional Information (from your form)
    description = models.TextField(blank=True, null=True)
    target_diseases = models.CharField(max_length=300, blank=True, null=True)
    age_groups = models.CharField(
        max_length=200, blank=True, null=True, help_text="Comma-separated age groups"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_stock")

    # Additional Information
    notes = models.TextField(blank=True, null=True)

    # Tracking
    received_date = models.DateField(
        blank=True, null=True, help_text="Date when vaccine was received"
    )
    received_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Staff who received the shipment",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vaccine__name", "expiration_date"]
        verbose_name_plural = "Vaccine Inventories"
        unique_together = [
            "lot_number",
            "vaccine",
        ]  # Prevent duplicate lot numbers for same vaccine

    def __str__(self):
        if self.vaccine:
            return f"{self.vaccine.name} - Lot: {self.lot_number}"
        return f"{self.vaccine_name} - Lot: {self.lot_number}"

    def save(self, *args, **kwargs):
        # Auto-update status based on stock levels
        if self.min_stock_level > 0:
            stock_percentage = (self.current_stock / self.min_stock_level) * 100

            if self.current_stock == 0:
                self.status = "out_of_stock"
            elif stock_percentage <= 20:
                self.status = "critical"
            elif stock_percentage <= 50:
                self.status = "low_stock"
            else:
                self.status = "in_stock"

        # If vaccine is linked, copy some information
        if self.vaccine and not self.vaccine_name:
            self.vaccine_name = self.vaccine.name
            self.vaccine_type = self.vaccine.vaccine_type
            self.target_diseases = self.vaccine.target_diseases
            self.age_groups = self.vaccine.age_groups
            self.storage_temperature = self.vaccine.storage_temperature
            self.manufacturer = self.vaccine.manufacturer

        super().save(*args, **kwargs)

    def is_expiring_soon(self):
        """Check if vaccine expires within 30 days"""
        if self.expiration_date:
            days_until_expiry = (self.expiration_date - date.today()).days
            return days_until_expiry <= 30
        return False

    def get_stock_percentage(self):
        """Get stock level as percentage of minimum stock"""
        if self.min_stock_level > 0:
            return min(100, (self.current_stock / self.min_stock_level) * 100)
        return 0

    def get_display_name(self):
        """Get display name for the vaccine"""
        return self.vaccine.name if self.vaccine else self.vaccine_name

    def get_age_groups_list(self):
        """Return age groups as a list"""
        if self.age_groups:
            return self.age_groups.split(",")
        return []


class VaccinationRecord(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("administered", "Administered"),
        ("missed", "Missed"),
        ("cancelled", "Cancelled"),
    ]

    REACTION_CHOICES = [
        ("none", "No Reaction"),
        ("mild", "Mild Reaction"),
        ("moderate", "Moderate Reaction"),
        ("severe", "Severe Reaction"),
    ]

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="vaccination_records"
    )
    vaccine = models.ForeignKey(
        Vaccine, on_delete=models.CASCADE, related_name="vaccination_records"
    )
    inventory_used = models.ForeignKey(
        VaccineInventory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vaccination_records",
    )

    # Dose Information
    dose_number = models.IntegerField(default=1, help_text="Which dose in the series")
    total_doses = models.IntegerField(
        default=1, help_text="Total doses required for this vaccine"
    )

    # Administration Details
    date_administered = models.DateField()
    next_due_date = models.DateField(blank=True, null=True)
    administered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administered_vaccinations",
        help_text="Medical professional who administered the vaccine",
    )
    administered_by_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of the person who administered the vaccine",
    )
    administering_facility = models.CharField(max_length=200, blank=True, null=True)
    lot_number = models.CharField(max_length=50, blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)

    # Status and Reactions
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="administered"
    )
    reaction = models.CharField(max_length=20, choices=REACTION_CHOICES, default="none")
    reaction_notes = models.TextField(blank=True, null=True)

    # Additional Information
    notes = models.TextField(blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)

    # Certificate Information
    certificate_number = models.CharField(
        max_length=50, blank=True, null=True, unique=True
    )
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_administered"]
        unique_together = ["patient", "vaccine", "dose_number"]
        verbose_name = "Vaccination Record"
        verbose_name_plural = "Vaccination Records"

    def __str__(self):
        return f"{self.patient} - {self.vaccine} (Dose {self.dose_number})"

    def save(self, *args, **kwargs):
        # Update inventory stock when vaccine is administered
        if self.status == "administered" and self.inventory_used:
            if self.inventory_used.current_stock > 0:
                self.inventory_used.current_stock -= 1
                self.inventory_used.save()

        # Auto-generate certificate number if not exists and status is administered
        if self.status == "administered" and not self.certificate_number:
            self.certificate_number = f"VAC-{self.patient.id}-{self.vaccine.id}-{self.date_administered.strftime('%Y%m%d')}"

        super().save(*args, **kwargs)

    def is_complete(self):
        return self.dose_number >= self.total_doses

    def is_overdue(self):
        if self.next_due_date and date.today() > self.next_due_date:
            return True
        return False

    def get_administered_by_display(self):
        """Return the display name of who administered the vaccine"""
        if self.administered_by:
            return self.administered_by.get_full_name() or self.administered_by.username
        elif self.administered_by_name:
            return self.administered_by_name
        return "Unknown"


class Appointment(models.Model):
    APPOINTMENT_STATUS = [
        ("scheduled", "Scheduled"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("no_show", "No Show"),
        ("rescheduled", "Rescheduled"),
    ]

    APPOINTMENT_TYPE = [
        ("vaccination", "Vaccination"),
        ("consultation", "Consultation"),
        ("checkup", "Regular Checkup"),
        ("followup", "Follow-up"),
        ("emergency", "Emergency"),
        ("other", "Other"),
    ]

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="appointments"
    )
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE)
    scheduled_date = models.DateTimeField()
    duration = models.IntegerField(default=30, help_text="Duration in minutes")
    status = models.CharField(
        max_length=20, choices=APPOINTMENT_STATUS, default="scheduled"
    )

    # Staff Information
    assigned_doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctor_appointments",
        limit_choices_to={"userprofile__user_type__in": ["doctor", "admin"]},
    )
    assigned_nurse = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nurse_appointments",
        limit_choices_to={"userprofile__user_type__in": ["nurse", "admin"]},
    )

    # Appointment Details
    reason = models.TextField(blank=True, null=True, help_text="Reason for appointment")
    symptoms = models.TextField(
        blank=True, null=True, help_text="Current symptoms if any"
    )
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")

    # Vaccination Specific (if appointment is for vaccination)
    vaccine = models.ForeignKey(
        Vaccine,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="appointments",
    )
    is_vaccination = models.BooleanField(default=False)

    # Reminders and Follow-up
    reminder_sent = models.BooleanField(default=False)
    follow_up_required = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_date"]
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"

    def __str__(self):
        return f"{self.patient} - {self.appointment_type} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"

    def is_upcoming(self):
        return (
            self.status in ["scheduled", "confirmed"]
            and self.scheduled_date > timezone.now()
        )

    def is_past_due(self):
        return (
            self.status in ["scheduled", "confirmed"]
            and self.scheduled_date < timezone.now()
        )

    def get_assigned_staff_display(self):
        """Get display name of assigned staff"""
        if self.assigned_doctor:
            try:
                return f"Dr. {self.assigned_doctor.get_full_name() or self.assigned_doctor.username}"
            except:
                return self.assigned_doctor.username
        elif self.assigned_nurse:
            try:
                return f"Nurse {self.assigned_nurse.get_full_name() or self.assigned_nurse.username}"
            except:
                return self.assigned_nurse.username
        return "Not assigned"


# =============================================
# RECOMMENDATION MODEL
# =============================================


class Recommendation(models.Model):
    """
    Model to store vaccine recommendations based on various factors
    """

    # ========== RECOMMENDATION STATUS ==========
    STATUS_CHOICES = [
        ("pending", "⏳ Pending Review"),
        ("approved", "✅ Approved"),
        ("rejected", "❌ Rejected"),
        ("implemented", "🎯 Implemented"),
        ("archived", "📦 Archived"),
    ]

    # ========== RECOMMENDATION PRIORITY ==========
    PRIORITY_CHOICES = [
        ("low", "🟢 Low"),
        ("medium", "🟡 Medium"),
        ("high", "🔴 High"),
        ("critical", "⚡ Critical"),
    ]

    # ========== RECOMMENDATION TYPES ==========
    RECOMMENDATION_TYPE_CHOICES = [
        ("restock", "📦 Restock Vaccine"),
        ("new_vaccine", "💉 New Vaccine Introduction"),
        ("dose_schedule", "📅 Dose Schedule Change"),
        ("storage", "❄️ Storage Requirement"),
        ("patient_outreach", "👥 Patient Outreach"),
        ("staff_training", "👨‍⚕️ Staff Training"),
        ("equipment", "🔧 Equipment Purchase"),
        ("policy", "📋 Policy Update"),
        ("expiring", "⚠️ Expiring Vaccine Alert"),
        ("other", "🔄 Other"),
    ]

    # ========== RELATIONSHIPS ==========
    vaccine = models.ForeignKey(
        Vaccine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
        help_text="Related vaccine (if applicable)",
    )
    vaccine_inventory = models.ForeignKey(
        VaccineInventory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
        help_text="Related inventory item (if applicable)",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_recommendations",
        help_text="User who created this recommendation",
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_recommendations",
        help_text="User who reviewed this recommendation",
    )

    # ========== RECOMMENDATION DETAILS ==========
    title = models.CharField(
        max_length=200, help_text="Short title of the recommendation"
    )
    description = models.TextField(
        help_text="Detailed description of the recommendation"
    )
    recommendation_type = models.CharField(
        max_length=50,
        choices=RECOMMENDATION_TYPE_CHOICES,
        default="other",
        help_text="Type of recommendation",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium",
        help_text="Priority level of this recommendation",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of the recommendation",
    )

    # ========== QUANTITY & COST INFORMATION ==========
    recommended_quantity = models.IntegerField(
        null=True, blank=True, help_text="Recommended quantity to order (if restock)"
    )
    current_stock = models.IntegerField(
        null=True, blank=True, help_text="Current stock level at time of recommendation"
    )
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated cost in USD",
    )

    # ========== TIMING INFORMATION ==========
    suggested_date = models.DateField(
        null=True, blank=True, help_text="Suggested date for implementation"
    )
    expiry_alert_date = models.DateField(
        null=True, blank=True, help_text="If related to expiring vaccines"
    )

    # ========== JUSTIFICATION & NOTES ==========
    justification = models.TextField(
        blank=True, help_text="Business/medical justification for this recommendation"
    )
    benefits = models.TextField(
        blank=True, help_text="Expected benefits if implemented"
    )
    risks = models.TextField(blank=True, help_text="Potential risks if not implemented")
    implementation_notes = models.TextField(
        blank=True, help_text="Notes on how to implement this recommendation"
    )

    # ========== REVIEW INFORMATION ==========
    review_notes = models.TextField(blank=True, help_text="Notes from the reviewer")
    review_date = models.DateTimeField(
        null=True, blank=True, help_text="When this recommendation was reviewed"
    )

    # ========== ATTACHMENTS & LINKS ==========
    attachment = models.FileField(
        upload_to="recommendation_attachments/",
        null=True,
        blank=True,
        help_text="Supporting document (PDF, image, etc.)",
    )
    reference_link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Reference URL for more information",
    )

    # ========== AUTOMATED RECOMMENDATION FLAGS ==========
    is_automated = models.BooleanField(
        default=False,
        help_text="Whether this was generated automatically by the system",
    )
    trigger_reason = models.CharField(
        max_length=100,
        blank=True,
        help_text="What triggered this automated recommendation (e.g., 'low_stock', 'expiring_soon')",
    )

    # ========== TIMESTAMPS ==========
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "-created_at"]
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["recommendation_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_recommendation_type_display()}: {self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-set current stock if related to inventory
        if self.vaccine_inventory and not self.current_stock:
            self.current_stock = self.vaccine_inventory.current_stock

        # Auto-set title if not provided
        if not self.title and self.vaccine:
            if self.recommendation_type == "restock":
                self.title = (
                    f"Restock {self.vaccine.name} - Current stock: {self.current_stock}"
                )
            elif self.recommendation_type == "expiring":
                self.title = (
                    f"Expiring {self.vaccine.name} - Expires: {self.expiry_alert_date}"
                )

        super().save(*args, **kwargs)

    def get_priority_color(self):
        """Return Bootstrap color class based on priority"""
        colors = {
            "low": "success",
            "medium": "warning",
            "high": "danger",
            "critical": "dark",
        }
        return colors.get(self.priority, "secondary")

    def get_status_color(self):
        """Return Bootstrap color class based on status"""
        colors = {
            "pending": "warning",
            "approved": "success",
            "rejected": "danger",
            "implemented": "info",
            "archived": "secondary",
        }
        return colors.get(self.status, "secondary")

    def days_since_created(self):
        """Return number of days since recommendation was created"""
        delta = timezone.now() - self.created_at
        return delta.days

    def is_overdue(self):
        """Check if recommendation is overdue based on suggested date"""
        if self.suggested_date and self.status == "pending":
            return timezone.now().date() > self.suggested_date
        return False


# =============================================
# SIGNAL HANDLERS - MERGED FROM BOTH FILES
# =============================================


# Your existing signal handlers
@receiver(post_save, sender=VaccineInventory)
def create_stock_recommendations(sender, instance, created, **kwargs):
    """
    Automatically create recommendations based on inventory status
    """
    # Check for low stock
    if instance.status in ["low_stock", "critical"]:
        # Check if a pending recommendation already exists
        existing = Recommendation.objects.filter(
            vaccine=instance.vaccine,
            vaccine_inventory=instance,
            recommendation_type="restock",
            status="pending",
        ).exists()

        if not existing:
            # Create restock recommendation
            Recommendation.objects.create(
                vaccine=instance.vaccine,
                vaccine_inventory=instance,
                title=f"Restock {instance.get_display_name()} - Low Stock Alert",
                description=f"Current stock is {instance.current_stock} doses. Minimum required is {instance.min_stock_level}. Please reorder soon.",
                recommendation_type="restock",
                priority="high" if instance.status == "critical" else "medium",
                status="pending",
                recommended_quantity=instance.min_stock_level
                * 2,  # Suggest ordering double the minimum
                current_stock=instance.current_stock,
                estimated_cost=instance.current_stock * 50,  # Rough estimate
                is_automated=True,
                trigger_reason=instance.status,
            )

    # Check for expiring soon
    if instance.is_expiring_soon():
        existing = Recommendation.objects.filter(
            vaccine=instance.vaccine,
            vaccine_inventory=instance,
            recommendation_type="expiring",
            status="pending",
        ).exists()

        if not existing:
            # Create expiration alert
            Recommendation.objects.create(
                vaccine=instance.vaccine,
                vaccine_inventory=instance,
                title=f"Vaccines Expiring Soon - {instance.get_display_name()}",
                description=f"Lot {instance.lot_number} expires on {instance.expiration_date}. Current stock: {instance.current_stock} doses.",
                recommendation_type="expiring",
                priority="high",
                status="pending",
                expiry_alert_date=instance.expiration_date,
                current_stock=instance.current_stock,
                is_automated=True,
                trigger_reason="expiring_soon",
            )


@receiver(post_save, sender=VaccinationRecord)
def create_vaccination_trend_recommendations(sender, instance, created, **kwargs):
    """
    Create recommendations based on vaccination trends
    """
    if created and instance.status == "administered":
        # Check if this vaccine is being used frequently
        recent_count = VaccinationRecord.objects.filter(
            vaccine=instance.vaccine,
            date_administered__gte=timezone.now() - timedelta(days=30),
        ).count()

        if recent_count > 50:  # Threshold for high usage
            # Check inventory for this vaccine
            inventories = VaccineInventory.objects.filter(
                vaccine=instance.vaccine, status__in=["low_stock", "critical"]
            )

            for inventory in inventories:
                existing = Recommendation.objects.filter(
                    vaccine=instance.vaccine,
                    vaccine_inventory=inventory,
                    recommendation_type="restock",
                    status="pending",
                ).exists()

                if not existing:
                    Recommendation.objects.create(
                        vaccine=instance.vaccine,
                        vaccine_inventory=inventory,
                        title=f"High Usage Alert - {instance.vaccine.name}",
                        description=f"This vaccine has been administered {recent_count} times in the last 30 days. Current stock may be insufficient.",
                        recommendation_type="restock",
                        priority="high",
                        status="pending",
                        recommended_quantity=recent_count,
                        current_stock=inventory.current_stock,
                        is_automated=True,
                        trigger_reason="high_usage",
                    )


# Common signal handlers (merged)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create UserProfile when a new User is created.
    Respects a `_pending_user_type` attribute set by the signup form,
    so the role is correct from the very first save.
    """
    if not created:
        return

    pending_role = getattr(instance, '_pending_user_type', 'patient')
    UserProfile.objects.get_or_create(
        user=instance,
        defaults={'user_type': pending_role},
    )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


# 3️⃣  THIRD — only 'patient' users get a Patient record
@receiver(post_save, sender=User)
def create_default_patient(sender, instance, created, **kwargs):
    """
    Create a default Patient record ONLY for users whose role is 'patient'.
    Healthcare workers and admins should NOT get a Patient record.
    """
    if not created:
        return

    profile = getattr(instance, "userprofile", None)
    if profile is None:
        return

    if profile.user_type != "patient":
        return

    Patient.objects.get_or_create(
        user=instance,
        defaults={
            "first_name": instance.first_name or "User",
            "last_name": instance.last_name or "Patient",
            "date_of_birth": date(2000, 1, 1),
            "gender": "U",
        },
    )


# 4️⃣  FOURTH — keep Patient records in sync when UserProfile changes
@receiver(post_save, sender=UserProfile)
def sync_patient_on_profile_save(sender, instance, created, **kwargs):
    """
    When a UserProfile is saved:
      - if user_type == 'patient'  → ensure a Patient record exists
      - otherwise                  → delete any stray Patient record
    """
    user = instance.user

    if instance.user_type == "patient":
        Patient.objects.get_or_create(
            user=user,
            defaults={
                "first_name": user.first_name or "User",
                "last_name": user.last_name or "Patient",
                "date_of_birth": date(2000, 1, 1),
                "gender": "U",
            },
        )
    else:
        # Not a patient anymore → remove any stray Patient record
        Patient.objects.filter(user=user).delete()


class VaccinationSchedule(models.Model):
    """
    Model to store vaccination schedule announcements for patients
    """

    title = models.CharField(max_length=200, help_text="Title of the vaccination event")
    description = models.TextField(
        help_text="Detailed description of the vaccination event"
    )
    vaccine = models.ForeignKey(
        Vaccine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schedules",
    )

    # Date and Time
    scheduled_date = models.DateField(help_text="Date of the vaccination event")
    start_time = models.TimeField(help_text="Start time of the event")
    end_time = models.TimeField(help_text="End time of the event")

    # Location
    location = models.CharField(
        max_length=200, help_text="Location where vaccination will take place"
    )
    address = models.TextField(help_text="Full address of the location")

    # Target audience
    target_age_groups = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Comma-separated age groups targeted",
    )
    is_for_all = models.BooleanField(
        default=True, help_text="Whether this is for all patients"
    )

    # Capacity and registration
    max_capacity = models.IntegerField(
        default=0, help_text="Maximum number of patients (0 for unlimited)"
    )
    registered_count = models.IntegerField(
        default=0, help_text="Number of patients registered"
    )
    requires_registration = models.BooleanField(
        default=True, help_text="Whether patients need to register"
    )

    # Status
    is_active = models.BooleanField(
        default=True, help_text="Whether this schedule is active"
    )
    is_published = models.BooleanField(
        default=False, help_text="Whether this schedule is published to patients"
    )

    # Additional information
    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes for patients"
    )
    contact_phone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Contact phone for inquiries"
    )
    contact_email = models.EmailField(
        blank=True, null=True, help_text="Contact email for inquiries"
    )

    # Metadata
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_schedules"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_date", "start_time"]
        verbose_name = "Vaccination Schedule"
        verbose_name_plural = "Vaccination Schedules"

    def __str__(self):
        return f"{self.title} - {self.scheduled_date}"

    def is_full(self):
        """Check if schedule is full"""
        if self.max_capacity > 0:
            return self.registered_count >= self.max_capacity
        return False

    def available_slots(self):
        """Get number of available slots"""
        if self.max_capacity > 0:
            return max(0, self.max_capacity - self.registered_count)
        return -1  # Unlimited


class Notification(models.Model):
    """
    Model to store notifications for users
    """

    NOTIFICATION_TYPES = [
        ("info", "Information"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("danger", "Alert"),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    is_for_all = models.BooleanField(default=False, help_text="Send to all patients")

    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, default="info"
    )

    # Related objects (optional)
    schedule = models.ForeignKey(
        "VaccinationSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    # Metadata
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.created_at}"


# =============================================
# VAXGUARD CORE MODELS
# Post-vaccination monitoring, IoT readings,
# symptom reporting, risk assessment, alerts
# =============================================


class Symptom(models.Model):
    """
    Master list of predefined symptoms that can be reported
    after vaccination. Stored in DB so admins can extend it.
    """

    SEVERITY_LEVEL_CHOICES = [
        ("mild", "🟢 Mild"),
        ("moderate", "🟡 Moderate"),
        ("severe", "🔴 Severe"),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    severity_level = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVEL_CHOICES,
        default="mild",
        help_text="Baseline severity of this symptom — used by the rule engine",
    )
    is_active = models.BooleanField(
        default=True, help_text="Inactive symptoms are hidden from reporting forms"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["severity_level", "name"]
        verbose_name = "Symptom"
        verbose_name_plural = "Symptoms"

    def __str__(self):
        return f"{self.name} ({self.get_severity_level_display()})"


class MonitoringSession(models.Model):
    """
    A post-vaccination observation session.
    Created after a VaccinationRecord is administered.
    Tracks the live status (GREEN/YELLOW/RED) and collects
    sensor readings + symptom reports for a period of time.
    """

    STATUS_CHOICES = [
        ("active", "🟢 Active"),
        ("completed", "✅ Completed"),
        ("cancelled", "❌ Cancelled"),
    ]

    CURRENT_LEVEL_CHOICES = [
        ("green", "🟢 Normal"),
        ("yellow", "🟡 Attention Required"),
        ("red", "🔴 Urgent Clinical Assessment Required"),
    ]

    # Core links
    vaccination_record = models.OneToOneField(
        VaccinationRecord,
        on_delete=models.CASCADE,
        related_name="monitoring_session",
        help_text="The vaccination that triggered this monitoring session",
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="monitoring_sessions",
    )
    started_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="started_monitoring_sessions",
        help_text="Healthcare worker who started this session",
    )

    # Timing
    start_time = models.DateTimeField(default=timezone.now)
    planned_duration_minutes = models.IntegerField(
        default=30,
        help_text="Planned monitoring duration in minutes (from vaccine default, can be overridden)",
    )
    end_time = models.DateTimeField(blank=True, null=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Current risk level (updated by rule engine; also logged to RiskAssessment)
    current_level = models.CharField(
        max_length=10,
        choices=CURRENT_LEVEL_CHOICES,
        default="green",
        help_text="Current risk level — updated automatically by the rule engine",
    )

    # Notes
    notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        verbose_name = "Monitoring Session"
        verbose_name_plural = "Monitoring Sessions"
        indexes = [
            models.Index(fields=["status", "current_level"]),
            models.Index(fields=["patient", "-start_time"]),
        ]

    def __str__(self):
        return f"Session #{self.id} — {self.patient.full_name()} ({self.get_current_level_display()})"

    def is_active(self):
        return self.status == "active"

    def elapsed_minutes(self):
        """Minutes elapsed since the session started."""
        if self.end_time:
            delta = self.end_time - self.start_time
        else:
            delta = timezone.now() - self.start_time
        return int(delta.total_seconds() // 60)

    def is_overdue(self):
        """Has the planned duration passed while still active?"""
        return (
            self.status == "active"
            and self.elapsed_minutes() >= self.planned_duration_minutes
        )


class SensorReading(models.Model):
    """
    A single IoT measurement from the ESP32 (or similar device).
    One row per reading — heart rate, SpO2, temperature.
    """

    session = models.ForeignKey(
        MonitoringSession,
        on_delete=models.CASCADE,
        related_name="sensor_readings",
    )
    device_id = models.CharField(
        max_length=100, help_text="Unique device identifier, e.g., 'esp32-ward-1'"
    )

    # Measurements
    heart_rate = models.IntegerField(
        blank=True, null=True, help_text="Beats per minute (BPM)"
    )
    spo2 = models.IntegerField(
        blank=True, null=True, help_text="Blood oxygen saturation (%, 0–100)"
    )
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Body temperature in °C",
    )

    # Device health (optional)
    battery_level = models.IntegerField(
        blank=True, null=True, help_text="Device battery level (%, 0–100)"
    )
    signal_strength = models.IntegerField(
        blank=True, null=True, help_text="Wi-Fi RSSI or similar (dBm)"
    )

    # When the reading was taken (may differ from when it reached the server)
    recorded_at = models.DateTimeField(default=timezone.now)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Sensor Reading"
        verbose_name_plural = "Sensor Readings"
        indexes = [
            models.Index(fields=["session", "-recorded_at"]),
            models.Index(fields=["device_id"]),
        ]

    def __str__(self):
        return f"Reading @ {self.recorded_at:%Y-%m-%d %H:%M:%S} (session #{self.session_id})"


class SymptomReport(models.Model):
    """
    A symptom reported during a monitoring session.
    Either by the patient themselves, or by an HCW on their behalf.
    """

    REPORTED_BY_CHOICES = [
        ("patient", "🧑 Patient"),
        ("healthcare_worker", "👨‍⚕️ Healthcare Worker"),
        ("caregiver", "👪 Caregiver"),
    ]

    session = models.ForeignKey(
        MonitoringSession,
        on_delete=models.CASCADE,
        related_name="symptom_reports",
    )
    symptom = models.ForeignKey(
        Symptom,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="symptom_reports",
        help_text="User who submitted this report",
    )
    reported_by_type = models.CharField(
        max_length=20,
        choices=REPORTED_BY_CHOICES,
        default="healthcare_worker",
    )
    notes = models.TextField(
        blank=True, null=True, help_text="Optional additional detail"
    )
    reported_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-reported_at"]
        verbose_name = "Symptom Report"
        verbose_name_plural = "Symptom Reports"
        indexes = [
            models.Index(fields=["session", "-reported_at"]),
        ]

    def __str__(self):
        return f"{self.symptom.name} — session #{self.session_id}"


class RiskAssessment(models.Model):
    """
    Snapshot of the rule-engine evaluation at a point in time.
    Every time readings/symptoms change, a new row is created.
    This provides the audit trail required by the VaxGuard spec.
    """

    LEVEL_CHOICES = [
        ("green", "🟢 Normal"),
        ("yellow", "🟡 Attention Required"),
        ("red", "🔴 Urgent Clinical Assessment Required"),
    ]

    session = models.ForeignKey(
        MonitoringSession,
        on_delete=models.CASCADE,
        related_name="risk_assessments",
    )
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    reason = models.TextField(
        help_text="Human-readable explanation of why this level was chosen"
    )
    triggered_rules = models.JSONField(
        default=list,
        blank=True,
        help_text="List of rule identifiers that fired (for audit / debugging)",
    )
    assessed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-assessed_at"]
        verbose_name = "Risk Assessment"
        verbose_name_plural = "Risk Assessments"
        indexes = [
            models.Index(fields=["session", "-assessed_at"]),
        ]

    def __str__(self):
        return f"Assessment [{self.level}] @ {self.assessed_at:%Y-%m-%d %H:%M:%S}"


class Alert(models.Model):
    """
    An emergency alert triggered when the rule engine reaches RED.
    Requires healthcare-worker acknowledgement and resolution.
    """

    LEVEL_CHOICES = [
        ("yellow", "🟡 Attention"),
        ("red", "🔴 Urgent"),
    ]
    STATUS_CHOICES = [
        ("new", "🆕 New"),
        ("acknowledged", "👀 Acknowledged"),
        ("under_assessment", "🩺 Under Assessment"),
        ("resolved", "✅ Resolved"),
        ("follow_up_required", "📅 Follow-up Required"),
    ]

    session = models.ForeignKey(
        MonitoringSession,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="red")
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="new")

    # What triggered it
    reason = models.TextField(
        help_text="What triggered this alert (copy of risk assessment reason)"
    )
    risk_assessment = models.ForeignKey(
        RiskAssessment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        help_text="The risk assessment snapshot that triggered this alert",
    )

    # Timeline
    created_at = models.DateTimeField(default=timezone.now)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
    )
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["level", "status"]),
        ]

    def __str__(self):
        return f"Alert #{self.id} [{self.get_level_display()}] — session #{self.session_id}"

    def acknowledgement_seconds(self):
        """Time between creation and acknowledgement, in seconds."""
        if self.acknowledged_at:
            return int((self.acknowledged_at - self.created_at).total_seconds())
        return None


class ClinicalResponse(models.Model):
    """
    Documentation of what the healthcare worker did in response to an alert.
    Does NOT prescribe treatment automatically — just records what was done.
    """

    alert = models.OneToOneField(
        Alert,
        on_delete=models.CASCADE,
        related_name="clinical_response",
    )
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="clinical_responses",
    )

    assessment_notes = models.TextField(help_text="What the healthcare worker observed")
    action_taken = models.TextField(
        help_text="What was done in response (e.g., 'Observed for 20 more minutes', 'Referred to hospital')"
    )
    referral_facility = models.CharField(
        max_length=200, blank=True, null=True, help_text="If referred, which facility"
    )
    additional_notes = models.TextField(blank=True, null=True)

    responded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-responded_at"]
        verbose_name = "Clinical Response"
        verbose_name_plural = "Clinical Responses"

    def __str__(self):
        return f"Response to alert #{self.alert_id}"


class Outcome(models.Model):
    """
    Final outcome of a monitoring session / alert.
    Records the end state of the patient — NOT a diagnosis.
    """

    OUTCOME_CHOICES = [
        ("resolved", "✅ Resolved — no further action"),
        ("observed", "👀 Continued observation"),
        ("referred", "🏥 Referred to facility"),
        ("follow_up", "📅 Follow-up required"),
        ("admitted", "🛏️ Admitted"),
        ("other", "🔄 Other"),
    ]

    session = models.OneToOneField(
        MonitoringSession,
        on_delete=models.CASCADE,
        related_name="outcome",
    )
    outcome_type = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    notes = models.TextField(blank=True, null=True)
    follow_up_date = models.DateField(
        blank=True,
        null=True,
        help_text="If outcome is 'follow_up', when should it happen",
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="recorded_outcomes",
    )
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Outcome"
        verbose_name_plural = "Outcomes"

    def __str__(self):
        return f"Outcome [{self.get_outcome_type_display()}] for session #{self.session_id}"
