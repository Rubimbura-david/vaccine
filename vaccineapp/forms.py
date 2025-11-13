# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Patient, Vaccine, VaccineInventory
from django.core.exceptions import ValidationError
from datetime import date

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

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        
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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Create a default patient record
            Patient.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                date_of_birth='2000-01-01',  # Default, can be updated later
                gender='O'
            )
        
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