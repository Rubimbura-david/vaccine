# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Patient, Vaccine, VaccineInventory, Recommendation
from django.core.exceptions import ValidationError
from datetime import date
from .models import VaccinationSchedule

# =============================================
# YOUR COLLEAGUE'S ADDITIONAL MODEL IMPORTS
# =============================================
from .models import Appointment, Consultation, Prescription, Medication, MedicalRecord, VaccinationRecord

# =============================================
# YOUR EXISTING FORMS - KEPT EXACTLY AS THEY WERE
# =============================================

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    
    # ========== NEW STATUS FIELD ==========
    USER_STATUS_CHOICES = [
        ('parent', '👪 Parent/Guardian'),
        ('doctor', '👨‍⚕️ Doctor'),
        ('nurse', '👩‍⚕️ Nurse'),
        ('admin', '👑 Administrator'),
    ]
    
    user_status = forms.ChoiceField(
        choices=USER_STATUS_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'user_status'
        }),
        label="I am a"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'user_status')
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Confirm your password'
        })
        
        # Add help text for status field
        self.fields['user_status'].help_text = "Select your role to determine your permissions in the system."

    def clean_user_status(self):
        """Validate that a valid status is selected"""
        user_status = self.cleaned_data.get('user_status')
        valid_statuses = [choice[0] for choice in self.USER_STATUS_CHOICES]
        
        if user_status not in valid_statuses:
            raise forms.ValidationError("Please select a valid user status.")
        
        return user_status

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # Get the selected user status
        user_status = self.cleaned_data.get('user_status', 'parent')
        
        if commit:
            user.save()
            
            # Create or update UserProfile with the user status
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'user_type': user_status}
            )
            
            # Create a default patient record for parents
            if user_status == 'parent':
                Patient.objects.create(
                    user=user,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    date_of_birth='2000-01-01',  # Default, can be updated later
                    gender='U'
                )
            
            # Set appropriate permissions based on user status
            if user_status == 'admin':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            elif user_status in ['doctor', 'nurse']:
                user.is_staff = True
                user.save()
        
        return user


class VaccineInventoryForm(forms.ModelForm):
    # Additional fields for direct entry (when not selecting existing vaccine)
    vaccine_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter vaccine name'
        })
    )
    
    # Age groups as multiple choice (from your HTML form)
    age_groups = forms.MultipleChoiceField(
        choices=[
            ('infant', 'Infant (0-12 months)'),
            ('toddler', 'Toddler (1-3 years)'),
            ('preschool', 'Preschool (3-5 years)'),
            ('school_age', 'School Age (6-12 years)'),
            ('adolescent', 'Adolescent (13-18 years)'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Recommended Age Groups'
    )
    
    # Storage temperature field
    storage_temperature = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2°C to 8°C'
        })
    )
    
    # Description field
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter vaccine description...'
        })
    )
    
    # Target diseases field
    target_diseases = forms.CharField(
        required=False,
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Diphtheria, Tetanus, Pertussis'
        })
    )

    class Meta:
        model = VaccineInventory
        fields = [
            'vaccine', 'vaccine_name', 'vaccine_type', 'manufacturer', 'lot_number',
            'current_stock', 'min_stock_level', 'doses_per_vial', 'expiration_date',
            'storage_temperature', 'description', 'target_diseases', 'age_groups', 'notes'
        ]
        widgets = {
            'vaccine': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select existing vaccine (optional)'
            }),
            'vaccine_type': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select vaccine type'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter manufacturer name'
            }),
            'lot_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter lot/batch number',
                'required': 'required'
            }),
            'current_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter current stock quantity',
                'min': '0',
                'required': 'required'
            }),
            'min_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter minimum stock level',
                'min': '1',
                'required': 'required'
            }),
            'doses_per_vial': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter doses per vial',
                'min': '1',
                'value': '1',
                'required': 'required'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': 'required'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any additional notes...'
            }),
        }
        labels = {
            'current_stock': 'Quantity',
            'min_stock_level': 'Minimum Stock Level',
            'doses_per_vial': 'Doses per Vial',
            'lot_number': 'Lot Number',
            'expiration_date': 'Expiry Date',
            'storage_temperature': 'Storage Temperature',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active vaccines in the dropdown
        self.fields['vaccine'].queryset = Vaccine.objects.filter(is_active=True)
        self.fields['vaccine'].required = False  # Make it optional
        
        # Make vaccine_name required if vaccine is not selected
        self.fields['vaccine_name'].required = False
        
        # Set required fields
        self.fields['vaccine_type'].required = True
        self.fields['manufacturer'].required = True
        self.fields['lot_number'].required = True
        self.fields['current_stock'].required = True
        self.fields['min_stock_level'].required = True
        self.fields['doses_per_vial'].required = True
        self.fields['expiration_date'].required = True
        self.fields['storage_temperature'].required = True

        # Add help text
        self.fields['vaccine'].help_text = "Select an existing vaccine or enter new vaccine details below"
        self.fields['vaccine_name'].help_text = "Required if no existing vaccine is selected"
        self.fields['current_stock'].help_text = "Current number of doses available"
        self.fields['min_stock_level'].help_text = "Alert when stock falls below this level"
        self.fields['doses_per_vial'].help_text = "Number of doses in each vial/container"
        self.fields['lot_number'].help_text = "Manufacturer's batch/lot number"
        self.fields['expiration_date'].help_text = "Vaccine expiration date"
        self.fields['storage_temperature'].help_text = "Required storage temperature range"

    def clean(self):
        cleaned_data = super().clean()
        vaccine = cleaned_data.get('vaccine')
        vaccine_name = cleaned_data.get('vaccine_name')
        
        # Either vaccine or vaccine_name must be provided
        if not vaccine and not vaccine_name:
            raise forms.ValidationError("You must either select an existing vaccine or enter a new vaccine name.")
        
        # If vaccine is selected, use its name
        if vaccine:
            cleaned_data['vaccine_name'] = vaccine.name
        
        # Convert age_groups list to comma-separated string for storage
        age_groups = cleaned_data.get('age_groups')
        if age_groups:
            cleaned_data['age_groups'] = ','.join(age_groups)
        
        return cleaned_data

    def clean_current_stock(self):
        current_stock = self.cleaned_data.get('current_stock')
        if current_stock is not None and current_stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return current_stock

    def clean_min_stock_level(self):
        min_stock_level = self.cleaned_data.get('min_stock_level')
        if min_stock_level is not None and min_stock_level < 1:
            raise forms.ValidationError("Minimum stock level must be at least 1.")
        return min_stock_level

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data.get('expiration_date')
        if expiration_date and expiration_date < date.today():
            raise forms.ValidationError("Expiration date cannot be in the past.")
        return expiration_date

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle the case where we have a vaccine name but no vaccine object
        if not instance.vaccine and self.cleaned_data.get('vaccine_name'):
            # Create a new Vaccine object if needed
            vaccine, created = Vaccine.objects.get_or_create(
                name=self.cleaned_data['vaccine_name'],
                defaults={
                    'vaccine_type': self.cleaned_data.get('vaccine_type', 'single'),
                    'manufacturer': self.cleaned_data.get('manufacturer', ''),
                    'description': self.cleaned_data.get('description', ''),
                    'target_diseases': self.cleaned_data.get('target_diseases', ''),
                    'age_groups': self.cleaned_data.get('age_groups', ''),
                    'storage_temperature': self.cleaned_data.get('storage_temperature', ''),
                }
            )
            instance.vaccine = vaccine
        
        if commit:
            instance.save()
        
        return instance


# =============================================
# RECOMMENDATION FORM
# =============================================

class RecommendationForm(forms.ModelForm):
    """
    Form for creating and managing vaccine recommendations
    """
    
    class Meta:
        model = Recommendation
        fields = [
            'title', 'description', 'recommendation_type', 'priority', 'status',
            'vaccine', 'vaccine_inventory', 'recommended_quantity', 'current_stock',
            'estimated_cost', 'suggested_date', 'expiry_alert_date',
            'justification', 'benefits', 'risks', 'implementation_notes',
            'attachment', 'reference_link', 'is_automated', 'trigger_reason'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter recommendation title',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the recommendation in detail...',
                'required': 'required'
            }),
            'recommendation_type': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'vaccine': forms.Select(attrs={
                'class': 'form-select'
            }),
            'vaccine_inventory': forms.Select(attrs={
                'class': 'form-select'
            }),
            'recommended_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter recommended quantity',
                'min': '0'
            }),
            'current_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current stock level',
                'min': '0',
                'readonly': True
            }),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estimated cost',
                'step': '0.01',
                'min': '0'
            }),
            'suggested_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_alert_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Why is this recommendation needed? Provide business/medical justification...'
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'What are the expected benefits if implemented?'
            }),
            'risks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'What are the potential risks if not implemented?'
            }),
            'implementation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'How should this recommendation be implemented?'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'reference_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'is_automated': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'trigger_reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., low_stock, expiring_soon, high_usage'
            }),
        }
        labels = {
            'title': 'Recommendation Title *',
            'description': 'Description *',
            'recommendation_type': 'Recommendation Type *',
            'priority': 'Priority Level *',
            'status': 'Status *',
            'vaccine': 'Related Vaccine',
            'vaccine_inventory': 'Related Inventory Item',
            'recommended_quantity': 'Recommended Quantity',
            'current_stock': 'Current Stock',
            'estimated_cost': 'Estimated Cost ($)',
            'suggested_date': 'Suggested Implementation Date',
            'expiry_alert_date': 'Expiry Alert Date',
            'justification': 'Justification',
            'benefits': 'Expected Benefits',
            'risks': 'Potential Risks',
            'implementation_notes': 'Implementation Notes',
            'attachment': 'Supporting Document',
            'reference_link': 'Reference Link',
            'is_automated': 'This is an automated recommendation',
            'trigger_reason': 'Trigger Reason',
        }
        help_texts = {
            'vaccine': 'Select a vaccine if this recommendation is vaccine-specific',
            'vaccine_inventory': 'Select an inventory item if this is about a specific batch',
            'recommended_quantity': 'Number of doses to order (for restock recommendations)',
            'current_stock': 'Current stock level (auto-filled if inventory selected)',
            'estimated_cost': 'Estimated cost in USD',
            'suggested_date': 'When should this be implemented?',
            'expiry_alert_date': 'If related to expiring vaccines',
            'attachment': 'Upload supporting documents (PDF, images, etc.)',
            'is_automated': 'Check if this was generated automatically by the system',
            'trigger_reason': 'What triggered this automated recommendation?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter querysets to show only active items
        self.fields['vaccine'].queryset = Vaccine.objects.filter(is_active=True)
        self.fields['vaccine'].required = False
        
        self.fields['vaccine_inventory'].queryset = VaccineInventory.objects.all()
        self.fields['vaccine_inventory'].required = False
        
        # Set default values for new recommendations
        if not self.instance.pk:  # If creating new object
            self.fields['status'].initial = 'pending'
            self.fields['priority'].initial = 'medium'
        
        # Make current_stock readonly (will be auto-filled)
        self.fields['current_stock'].widget.attrs['readonly'] = True
        
        # Add CSS classes for better styling
        for field_name, field in self.fields.items():
            if field_name not in ['is_automated', 'attachment']:
                if field_name in ['description', 'justification', 'benefits', 'risks', 'implementation_notes']:
                    field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' rich-textarea'

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that if restock type, recommended_quantity is provided
        rec_type = cleaned_data.get('recommendation_type')
        recommended_quantity = cleaned_data.get('recommended_quantity')
        
        if rec_type == 'restock' and not recommended_quantity:
            raise forms.ValidationError({
                'recommended_quantity': 'Recommended quantity is required for restock recommendations.'
            })
        
        # Validate that if expiring type, expiry_alert_date is provided
        if rec_type == 'expiring' and not cleaned_data.get('expiry_alert_date'):
            raise forms.ValidationError({
                'expiry_alert_date': 'Expiry alert date is required for expiring vaccine recommendations.'
            })
        
        # Validate dates
        suggested_date = cleaned_data.get('suggested_date')
        expiry_date = cleaned_data.get('expiry_alert_date')
        today = date.today()
        
        if suggested_date and suggested_date < today:
            raise forms.ValidationError({
                'suggested_date': 'Suggested date cannot be in the past.'
            })
        
        if expiry_date and expiry_date < today:
            raise forms.ValidationError({
                'expiry_alert_date': 'Expiry alert date cannot be in the past.'
            })
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Auto-fill current_stock if vaccine_inventory is selected
        if instance.vaccine_inventory and not instance.current_stock:
            instance.current_stock = instance.vaccine_inventory.current_stock
        
        # Auto-generate title if not provided
        if not instance.title and instance.vaccine:
            if instance.recommendation_type == 'restock':
                instance.title = f"Restock {instance.vaccine.name}"
            elif instance.recommendation_type == 'expiring':
                instance.title = f"Expiring {instance.vaccine.name}"
            else:
                instance.title = f"Recommendation for {instance.vaccine.name}"
        
        if commit:
            instance.save()
            # Save many-to-many relationships if any
            self.save_m2m()
        
        return instance


# =============================================
# YOUR COLLEAGUE'S ADDITIONAL FORMS - ADDED BELOW
# =============================================

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'appointment_type', 'scheduled_date', 'duration', 'reason', 'symptoms', 'assigned_doctor', 'vaccine']
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'symptoms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'assigned_doctor': forms.Select(attrs={'class': 'form-control'}),
            'vaccine': forms.Select(attrs={'class': 'form-control'}),
        }


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['patient', 'doctor', 'symptoms', 'description', 'diagnosis', 'recommendations', 'follow_up_date']
        widgets = {
            'symptoms': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'recommendations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
        }


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient', 'doctor', 'diagnosis', 'symptoms', 'medical_advice', 'follow_up', 'pharmacy_notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'symptoms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'medical_advice': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'follow_up': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'pharmacy_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
        }


class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ['name', 'dosage', 'frequency', 'duration', 'instructions', 'purpose']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
        }


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['patient', 'full_name', 'date_of_birth', 'age', 'gender', 'blood_type', 
                 'allergies', 'emergency_contact', 'address', 'phone', 'email', 
                 'insurance_number', 'primary_physician']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'age': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'emergency_contact': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'insurance_number': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_physician': forms.TextInput(attrs={'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
        }


class VaccinationRecordForm(forms.ModelForm):
    class Meta:
        model = VaccinationRecord
        fields = ['patient', 'vaccine', 'dose_number', 'total_doses', 'date_administered', 
                 'next_due_date', 'administered_by', 'administering_facility', 'lot_number', 
                 'expiration_date', 'status', 'reaction', 'reaction_notes', 'notes']
        widgets = {
            'date_administered': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'administered_by': forms.TextInput(attrs={'class': 'form-control'}),
            'administering_facility': forms.TextInput(attrs={'class': 'form-control'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'reaction_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'vaccine': forms.Select(attrs={'class': 'form-control'}),
            'dose_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_doses': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'reaction': forms.Select(attrs={'class': 'form-control'}),
        }

class VaccinationScheduleForm(forms.ModelForm):
    class Meta:
        model = VaccinationSchedule
        fields = [
            'title', 'description', 'vaccine', 'scheduled_date', 
            'start_time', 'end_time', 'location', 'address',
            'target_age_groups', 'is_for_all', 'max_capacity',
            'requires_registration', 'is_published', 'notes',
            'contact_phone', 'contact_email'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Monthly Childhood Vaccination Drive'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the vaccination event...'}),
            'vaccine': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Community Health Center'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address...'}),
            'target_age_groups': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0-2 years, 5-12 years'}),
            'is_for_all': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'requires_registration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes...'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +1234567890'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g., clinic@example.com'}),
        }
        labels = {
            'target_age_groups': 'Target Age Groups',
            'is_for_all': 'Available for all patients',
            'max_capacity': 'Maximum Capacity (0 for unlimited)',
            'requires_registration': 'Requires registration',
            'is_published': 'Publish to patients',
        }
        help_texts = {
            'target_age_groups': 'Comma-separated list of age groups (leave blank if for all)',
            'max_capacity': 'Set to 0 for unlimited capacity',
        }