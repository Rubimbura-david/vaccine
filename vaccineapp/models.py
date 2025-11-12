from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from django.utils import timezone  # Added missing import

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
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
    
    # Profile Image
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('U', 'Unknown'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('UNK', 'Unknown'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patients')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Height in cm")
    
    # Medical Information
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True, help_text="List any known allergies")
    medical_conditions = models.TextField(blank=True, null=True, help_text="List any medical conditions")
    current_medications = models.TextField(blank=True, null=True, help_text="List current medications")
    
    # Contact Information
    patient_phone = models.CharField(max_length=15, blank=True, null=True)
    patient_email = models.EmailField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Vaccine(models.Model):
    VACCINE_TYPE_CHOICES = [
        ('routine', 'Routine Childhood'),
        ('travel', 'Travel'),
        ('seasonal', 'Seasonal'),
        ('special', 'Special Condition'),
    ]
    
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    vaccine_type = models.CharField(max_length=20, choices=VACCINE_TYPE_CHOICES, default='routine')
    recommended_age = models.CharField(max_length=100, blank=True, null=True)
    doses_required = models.IntegerField(default=1)
    days_between_doses = models.IntegerField(blank=True, null=True, help_text="Days between doses")
    booster_required = models.BooleanField(default=False)
    booster_frequency = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Every 10 years")
    
    # Vaccine Information
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    storage_temperature = models.CharField(max_length=50, blank=True, null=True)
    contraindications = models.TextField(blank=True, null=True)
    side_effects = models.TextField(blank=True, null=True)
    
    # Administration
    route = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Intramuscular, Oral")
    site = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Upper arm, Thigh")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class VaccinationRecord(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('administered', 'Administered'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ]
    
    REACTION_CHOICES = [
        ('none', 'No Reaction'),
        ('mild', 'Mild Reaction'),
        ('moderate', 'Moderate Reaction'),
        ('severe', 'Severe Reaction'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vaccination_records')
    vaccine = models.ForeignKey(Vaccine, on_delete=models.CASCADE, related_name='vaccination_records')
    
    # Dose Information
    dose_number = models.IntegerField(default=1, help_text="Which dose in the series")
    total_doses = models.IntegerField(default=1, help_text="Total doses required for this vaccine")
    
    # Administration Details
    date_administered = models.DateField()
    next_due_date = models.DateField(blank=True, null=True)
    administered_by = models.CharField(max_length=100, blank=True, null=True)
    administering_facility = models.CharField(max_length=200, blank=True, null=True)
    lot_number = models.CharField(max_length=50, blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    
    # Status and Reactions
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='administered')
    reaction = models.CharField(max_length=20, choices=REACTION_CHOICES, default='none')
    reaction_notes = models.TextField(blank=True, null=True)
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_administered']
        unique_together = ['patient', 'vaccine', 'dose_number']
    
    def __str__(self):
        return f"{self.patient} - {self.vaccine} (Dose {self.dose_number})"
    
    def is_complete(self):
        return self.dose_number >= self.total_doses
    
    def is_overdue(self):
        if self.next_due_date and date.today() > self.next_due_date:
            return True
        return False


class Appointment(models.Model):
    APPOINTMENT_STATUS = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    APPOINTMENT_TYPE = [
        ('vaccination', 'Vaccination'),
        ('consultation', 'Consultation'),
        ('checkup', 'Regular Checkup'),
        ('followup', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE)
    scheduled_date = models.DateTimeField()
    duration = models.IntegerField(default=30, help_text="Duration in minutes")
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS, default='scheduled')
    
    # Staff Information
    assigned_doctor = models.CharField(max_length=100, blank=True, null=True)
    assigned_nurse = models.CharField(max_length=100, blank=True, null=True)
    
    # Appointment Details
    reason = models.TextField(blank=True, null=True, help_text="Reason for appointment")
    symptoms = models.TextField(blank=True, null=True, help_text="Current symptoms if any")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    
    # Vaccination Specific (if appointment is for vaccination)
    vaccine = models.ForeignKey(Vaccine, on_delete=models.SET_NULL, blank=True, null=True, related_name='appointments')
    is_vaccination = models.BooleanField(default=False)
    
    # Reminders and Follow-up
    reminder_sent = models.BooleanField(default=False)
    follow_up_required = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_date']
    
    def __str__(self):
        return f"{self.patient} - {self.appointment_type} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
    
    def is_upcoming(self):
        return self.status in ['scheduled', 'confirmed'] and self.scheduled_date > timezone.now()
    
    def is_past_due(self):
        return self.status in ['scheduled', 'confirmed'] and self.scheduled_date < timezone.now()


# Fixed Signal Handlers
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create UserProfile when a new User is created
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save UserProfile when User is saved
    """
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


# Additional signal to create default patient for new users
@receiver(post_save, sender=User)
def create_default_patient(sender, instance, created, **kwargs):
    """
    Create a default patient record for new users
    """
    if created:
        Patient.objects.get_or_create(
            user=instance,
            first_name=instance.first_name or 'User',
            last_name=instance.last_name or 'Patient',
            date_of_birth=date(2000, 1, 1),  # Default date
            gender='U'
        )