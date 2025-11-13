from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone
from datetime import timedelta, date
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from .forms import CustomUserCreationForm, VaccineInventoryForm
from .models import UserProfile, Patient, Vaccine, VaccinationRecord, Appointment, VaccineInventory

# =============================================
# CACHE CONTROL DECORATOR
# =============================================

def no_cache_after_logout(view_func):
    """
    Decorator to add no-cache headers to prevent back button after logout
    """
    def wrapped_view(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
    return wrapped_view

# =============================================
# PROTECTED PAGES - REQUIRE LOGIN WITH CACHE CONTROL
# =============================================

@login_required(login_url='/login/')
@no_cache_after_logout
def index(request):
    """Home page - requires login"""
    return render(request, 'index.html')

@login_required(login_url='/login/')
@no_cache_after_logout
def about(request):
    """About page - requires login"""
    return render(request, 'about.html')

@login_required(login_url='/login/')
@no_cache_after_logout
def contact(request):
    """Contact page - requires login"""
    return render(request, 'contact.html')

@login_required(login_url='/login/')
@no_cache_after_logout
def service(request):
    """Services page - requires login"""
    return render(request, 'service.html')

@login_required(login_url='/login/')
@no_cache_after_logout
def vaccine(request):
    """Vaccine information page - requires login"""
    # Get all vaccines from database
    vaccines = Vaccine.objects.filter(is_active=True)
    return render(request, 'vaccine.html', {'vaccines': vaccines})

@login_required(login_url='/login/')
@no_cache_after_logout
def dashboard(request):
    """Dashboard page - requires login"""
    user = request.user
    
    # Patient statistics
    patients_count = Patient.objects.filter(user=user).count()
    appointments_count = Appointment.objects.filter(patient__user=user, status='scheduled').count()
    vaccination_records_count = VaccinationRecord.objects.filter(patient__user=user).count()
    
    # Recent appointments
    recent_appointments = Appointment.objects.filter(
        patient__user=user, 
        status='scheduled'
    ).order_by('scheduled_date')[:5]
    
    # ============ VACCINE INVENTORY DATA FOR DASHBOARD ============
    # Get vaccine inventory data (for all users in the system)
    vaccine_inventory = VaccineInventory.objects.select_related('vaccine').all()
    
    # Calculate vaccine statistics
    total_vaccines = vaccine_inventory.count()
    total_doses = sum(item.current_stock for item in vaccine_inventory)
    
    # Count low stock items (critical and low_stock status)
    low_stock_count = vaccine_inventory.filter(
        status__in=['low_stock', 'critical']
    ).count()
    
    # Count unique vaccine types
    vaccine_types = vaccine_inventory.values('vaccine__vaccine_type').distinct().count()
    
    # Total administered vaccines (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    total_administered = VaccinationRecord.objects.filter(
        status='administered',
        date_administered__gte=thirty_days_ago
    ).count()
    
    # Additional dashboard statistics
    today = timezone.now().date()
    
    # Today's vaccinations
    todays_vaccinations = VaccinationRecord.objects.filter(
        date_administered=today,
        status='administered'
    ).count()
    
    # Vaccinations due (scheduled for today)
    vaccinations_due = VaccinationRecord.objects.filter(
        date_administered=today,
        status='scheduled'
    ).count()
    
    # Overdue vaccinations
    overdue_vaccinations = VaccinationRecord.objects.filter(
        date_administered__lt=today,
        status='scheduled'
    ).count()
    
    # Vaccine coverage percentage (patients with at least one vaccination)
    total_patients = Patient.objects.count()
    patients_vaccinated = Patient.objects.filter(
        vaccination_records__status='administered'
    ).distinct().count()
    
    if total_patients > 0:
        vaccine_coverage = (patients_vaccinated / total_patients) * 100
    else:
        vaccine_coverage = 0
    
    # Recent vaccination activity
    recent_vaccinations = VaccinationRecord.objects.filter(
        status='administered'
    ).select_related('patient', 'vaccine').order_by('-date_administered')[:10]
    
    # Today's schedule
    todays_schedule = Appointment.objects.filter(
        scheduled_date__date=today,
        status__in=['scheduled', 'confirmed']
    ).select_related('patient').order_by('scheduled_date')
    
    # Age distribution data for charts
    age_distribution = {
        '0-1': Patient.objects.filter(
            date_of_birth__gte=today - timedelta(days=365)
        ).count(),
        '1-3': Patient.objects.filter(
            date_of_birth__gte=today - timedelta(days=3*365),
            date_of_birth__lt=today - timedelta(days=365)
        ).count(),
        '3-6': Patient.objects.filter(
            date_of_birth__gte=today - timedelta(days=6*365),
            date_of_birth__lt=today - timedelta(days=3*365)
        ).count(),
        '6-12': Patient.objects.filter(
            date_of_birth__gte=today - timedelta(days=12*365),
            date_of_birth__lt=today - timedelta(days=6*365)
        ).count(),
        '12-18': Patient.objects.filter(
            date_of_birth__gte=today - timedelta(days=18*365),
            date_of_birth__lt=today - timedelta(days=12*365)
        ).count(),
    }
    
    # Vaccine type distribution
    vaccine_type_stats = {}
    for vaccine_type, display_name in Vaccine.VACCINE_TYPE_CHOICES:
        count = Vaccine.objects.filter(vaccine_type=vaccine_type, is_active=True).count()
        vaccine_type_stats[vaccine_type] = {
            'count': count,
            'display_name': display_name
        }
    
    context = {
        # Original context
        'patients_count': patients_count,
        'appointments_count': appointments_count,
        'vaccination_records_count': vaccination_records_count,
        'recent_appointments': recent_appointments,
        
        # Vaccine inventory data for dashboard
        'vaccine_inventory': vaccine_inventory,
        'total_vaccines': total_vaccines,
        'total_doses': total_doses,
        'low_stock_count': low_stock_count,
        'vaccine_types': vaccine_types,
        'total_administered': total_administered,
        
        # Additional dashboard stats
        'todays_vaccinations': todays_vaccinations,
        'vaccinations_due': vaccinations_due,
        'overdue_vaccinations': overdue_vaccinations,
        'vaccine_coverage': round(vaccine_coverage, 1),
        'recent_vaccinations': recent_vaccinations,
        'todays_schedule': todays_schedule,
        'age_distribution': age_distribution,
        'vaccine_type_stats': vaccine_type_stats,
        'total_patients': total_patients,
        'patients_vaccinated': patients_vaccinated,
    }
    
    response = render(request, 'dashboard.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required(login_url='/login/')
@no_cache_after_logout
def profile_view(request):
    """User profile page - requires login"""
    # Get user profile and related data
    user = request.user
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = None
    
    patients = Patient.objects.filter(user=user)
    upcoming_appointments = Appointment.objects.filter(
        patient__user=user, 
        status='scheduled'
    ).order_by('scheduled_date')[:5]
    
    context = {
        'profile': profile,
        'patients': patients,
        'upcoming_appointments': upcoming_appointments,
    }
    response = render(request, 'profile.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# =============================================
# VACCINE INVENTORY MANAGEMENT
# =============================================

@login_required(login_url='/login/')
@no_cache_after_logout
def vaccine_inventory(request):
    """Vaccine inventory management page"""
    # Handle form submission
    if request.method == 'POST':
        form = VaccineInventoryForm(request.POST)
        if form.is_valid():
            try:
                vaccine_inventory = form.save()
                vaccine_name = vaccine_inventory.get_display_name()
                messages.success(request, f'Successfully added {vaccine_name} to inventory!')
                return redirect('vaccine_inventory')
            except Exception as e:
                messages.error(request, f'Error saving vaccine: {str(e)}')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = VaccineInventoryForm()
    
    # Get all vaccine inventory items
    vaccine_inventory = VaccineInventory.objects.select_related('vaccine').all()
    
    # Calculate statistics
    total_vaccines = vaccine_inventory.count()
    vaccine_types = Vaccine.objects.values('vaccine_type').distinct().count()
    total_doses = sum(item.current_stock for item in vaccine_inventory)
    
    # Calculate doses administered this month
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    doses_this_month = VaccinationRecord.objects.filter(
        date_administered__gte=start_of_month,
        status='administered'
    ).count()
    
    # Low stock count (critical + low stock)
    low_stock_count = vaccine_inventory.filter(
        status__in=['low_stock', 'critical']
    ).count()
    
    # Total administered
    total_administered = VaccinationRecord.objects.filter(status='administered').count()
    
    # Administered this week
    start_of_week = timezone.now() - timedelta(days=timezone.now().weekday())
    administered_this_week = VaccinationRecord.objects.filter(
        date_administered__gte=start_of_week,
        status='administered'
    ).count()
    
    # Expiring soon (within 30 days)
    expiring_soon_count = sum(1 for item in vaccine_inventory if item.is_expiring_soon())
    
    context = {
        'vaccine_inventory': vaccine_inventory,
        'form': form,
        'vaccines': Vaccine.objects.filter(is_active=True),
        'total_vaccines': total_vaccines,
        'vaccine_types': vaccine_types,
        'total_doses': total_doses,
        'doses_this_month': doses_this_month,
        'low_stock_count': low_stock_count,
        'total_administered': total_administered,
        'administered_this_week': administered_this_week,
        'expiring_soon_count': expiring_soon_count,
    }
    
    response = render(request, 'vaccine_inventory.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@csrf_exempt
@require_POST
@login_required(login_url='/login/')
def create_vaccine_api(request):
    """API endpoint to create new vaccine from frontend form"""
    try:
        data = json.loads(request.body)
        
        # Handle age groups (convert from list to comma-separated string)
        age_groups = data.get('ageGroups', [])
        if isinstance(age_groups, list):
            age_groups_str = ','.join(age_groups)
        else:
            age_groups_str = age_groups
        
        # Create Vaccine if it doesn't exist
        vaccine_name = data.get('vaccineName')
        vaccine_type = data.get('vaccineType')
        manufacturer = data.get('manufacturer')
        
        # Check if vaccine already exists
        existing_vaccine = Vaccine.objects.filter(name=vaccine_name).first()
        if existing_vaccine:
            vaccine = existing_vaccine
        else:
            # Create new Vaccine
            vaccine = Vaccine.objects.create(
                name=vaccine_name,
                vaccine_type=vaccine_type,
                manufacturer=manufacturer,
                storage_temperature=data.get('storageTemp'),
                description=data.get('description'),
                target_diseases=data.get('targetDiseases'),
                age_groups=age_groups_str,
                doses_required=1,
                is_active=True
            )
        
        # Create VaccineInventory
        inventory = VaccineInventory.objects.create(
            vaccine=vaccine,
            vaccine_name=vaccine_name,  # Store name directly as well
            vaccine_type=vaccine_type,
            manufacturer=manufacturer,
            lot_number=data.get('lotNumber'),
            current_stock=int(data.get('quantity', 0)),
            min_stock_level=int(data.get('minStock', 10)),
            doses_per_vial=int(data.get('dosesPerVial', 1)),
            expiration_date=data.get('expiryDate'),
            storage_temperature=data.get('storageTemp'),
            description=data.get('description'),
            target_diseases=data.get('targetDiseases'),
            age_groups=age_groups_str
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Vaccine added successfully!',
            'vaccine_id': vaccine.id,
            'vaccine_name': vaccine.name,
            'inventory_id': inventory.id
        })
        
    except Exception as e:
        import traceback
        print(f"Error creating vaccine: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)

@login_required(login_url='/login/')
@no_cache_after_logout
def edit_vaccine_inventory(request, inventory_id):
    """Edit existing vaccine inventory item"""
    inventory_item = get_object_or_404(VaccineInventory, id=inventory_id)
    
    if request.method == 'POST':
        form = VaccineInventoryForm(request.POST, instance=inventory_item)
        if form.is_valid():
            try:
                form.save()
                vaccine_name = inventory_item.get_display_name()
                messages.success(request, f'Successfully updated {vaccine_name} inventory!')
                return redirect('vaccine_inventory')
            except Exception as e:
                messages.error(request, f'Error updating vaccine: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-populate age_groups from comma-separated string to list
        initial_data = {}
        if inventory_item.age_groups:
            initial_data['age_groups'] = inventory_item.age_groups.split(',')
        
        form = VaccineInventoryForm(instance=inventory_item, initial=initial_data)
    
    context = {
        'form': form,
        'inventory_item': inventory_item,
        'vaccines': Vaccine.objects.filter(is_active=True),
    }
    return render(request, 'edit_vaccine_inventory.html', context)

@login_required(login_url='/login/')
@no_cache_after_logout
def delete_vaccine_inventory(request, inventory_id):
    """Delete vaccine inventory item"""
    inventory_item = get_object_or_404(VaccineInventory, id=inventory_id)
    vaccine_name = inventory_item.get_display_name()
    
    if request.method == 'POST':
        inventory_item.delete()
        messages.success(request, f'Successfully deleted {vaccine_name} from inventory!')
        return redirect('vaccine_inventory')
    
    context = {
        'inventory_item': inventory_item,
    }
    return render(request, 'delete_vaccine_inventory.html', context)

@login_required(login_url='/login/')
@no_cache_after_logout
def vaccine_details(request, inventory_id):
    """View detailed information about a specific vaccine"""
    inventory_item = get_object_or_404(VaccineInventory, id=inventory_id)
    
    # Get administration history for this vaccine
    administration_history = VaccinationRecord.objects.filter(
        vaccine=inventory_item.vaccine
    ).select_related('patient').order_by('-date_administered')[:10]
    
    context = {
        'inventory_item': inventory_item,
        'administration_history': administration_history,
    }
    return render(request, 'vaccine_details.html', context)

# =============================================
# VACCINE API ENDPOINTS
# =============================================

@require_http_methods(["GET"])
@login_required(login_url='/login/')
def vaccine_detail_api(request, vaccine_id):
    """API endpoint to get vaccine details"""
    try:
        vaccine = VaccineInventory.objects.get(id=vaccine_id)
        
        data = {
            'id': vaccine.id,
            'name': vaccine.get_display_name(),
            'vaccine_type': vaccine.vaccine.vaccine_type if vaccine.vaccine else vaccine.vaccine_type,
            'vaccine_type_display': vaccine.vaccine.get_vaccine_type_display() if vaccine.vaccine else vaccine.get_vaccine_type_display(),
            'manufacturer': vaccine.vaccine.manufacturer if vaccine.vaccine and vaccine.vaccine.manufacturer else vaccine.manufacturer or 'Not specified',
            'lot_number': vaccine.lot_number or 'Not specified',
            'target_diseases': vaccine.vaccine.target_diseases if vaccine.vaccine else vaccine.target_diseases or 'Not specified',
            'current_stock': vaccine.current_stock,
            'minimum_stock': vaccine.min_stock_level,
            'status': vaccine.status,
            'expiration_date': vaccine.expiration_date.isoformat() if vaccine.expiration_date else None,
            'storage_temperature': vaccine.storage_temperature or 'Not specified',
            'description': vaccine.vaccine.description if vaccine.vaccine else vaccine.description or 'No description available',
            'administered_count': vaccine.vaccine.get_administered_count() if vaccine.vaccine else 0,
            'doses_per_vial': vaccine.doses_per_vial,
        }
        
        return JsonResponse(data)
        
    except VaccineInventory.DoesNotExist:
        return JsonResponse({'error': 'Vaccine not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["DELETE"])
@csrf_exempt
@login_required(login_url='/login/')
def delete_vaccine_api(request, vaccine_id):
    """API endpoint to delete a vaccine"""
    try:
        vaccine = VaccineInventory.objects.get(id=vaccine_id)
        vaccine_name = vaccine.get_display_name()
        vaccine.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Vaccine {vaccine_name} deleted successfully'
        })
        
    except VaccineInventory.DoesNotExist:
        return JsonResponse({'error': 'Vaccine not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
@login_required(login_url='/login/')
def update_vaccine_api(request, vaccine_id):
    """API endpoint to update a vaccine"""
    try:
        vaccine = VaccineInventory.objects.get(id=vaccine_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'current_stock' in data:
            vaccine.current_stock = int(data['current_stock'])
        if 'min_stock_level' in data:
            vaccine.min_stock_level = int(data['min_stock_level'])
        if 'expiration_date' in data:
            vaccine.expiration_date = data['expiration_date']
        if 'storage_temperature' in data:
            vaccine.storage_temperature = data['storage_temperature']
        if 'description' in data:
            vaccine.description = data['description']
        if 'lot_number' in data:
            vaccine.lot_number = data['lot_number']
        
        vaccine.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Vaccine {vaccine.get_display_name()} updated successfully'
        })
        
    except VaccineInventory.DoesNotExist:
        return JsonResponse({'error': 'Vaccine not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =============================================
# PATIENT MANAGEMENT
# =============================================

@login_required(login_url='/login/')
@no_cache_after_logout
def patient_list(request):
    """List all patients for the current user"""
    patients = Patient.objects.filter(user=request.user).select_related('user')
    
    # Calculate statistics
    total_patients = patients.count()
    patients_with_complete_vaccinations = sum(1 for patient in patients if patient.vaccination_records.filter(status='administered').exists())
    
    context = {
        'patients': patients,
        'total_patients': total_patients,
        'patients_with_complete_vaccinations': patients_with_complete_vaccinations,
    }
    return render(request, 'patient_list.html', context)

@login_required(login_url='/login/')
@no_cache_after_logout
def vaccination_schedule(request):
    """Vaccination schedule view"""
    # Get upcoming vaccinations
    upcoming_vaccinations = VaccinationRecord.objects.filter(
        patient__user=request.user,
        status='scheduled',
        date_administered__gte=date.today()
    ).select_related('patient', 'vaccine').order_by('date_administered')
    
    # Get overdue vaccinations
    overdue_vaccinations = VaccinationRecord.objects.filter(
        patient__user=request.user,
        status='scheduled',
        date_administered__lt=date.today()
    ).select_related('patient', 'vaccine').order_by('date_administered')
    
    context = {
        'upcoming_vaccinations': upcoming_vaccinations,
        'overdue_vaccinations': overdue_vaccinations,
    }
    return render(request, 'vaccination_schedule.html', context)

@login_required(login_url='/login/')
@no_cache_after_logout
def immunization_records(request):
    """Immunization records view"""
    records = VaccinationRecord.objects.filter(
        patient__user=request.user
    ).select_related('patient', 'vaccine').order_by('-date_administered')
    
    # Group by patient
    patients_with_records = {}
    for record in records:
        if record.patient not in patients_with_records:
            patients_with_records[record.patient] = []
        patients_with_records[record.patient].append(record)
    
    context = {
        'patients_with_records': patients_with_records,
        'total_records': records.count(),
    }
    return render(request, 'immunization_records.html', context)

@login_required(login_url='/login/')
@no_cache_after_logout
def coverage_analytics(request):
    """Vaccine coverage analytics"""
    # Get vaccination statistics
    total_vaccinations = VaccinationRecord.objects.filter(
        patient__user=request.user,
        status='administered'
    ).count()
    
    # Get vaccine coverage by type
    vaccine_coverage = {}
    for vaccine in Vaccine.objects.filter(is_active=True):
        administered_count = VaccinationRecord.objects.filter(
            patient__user=request.user,
            vaccine=vaccine,
            status='administered'
        ).count()
        total_patients = Patient.objects.filter(user=request.user).count()
        
        if total_patients > 0:
            coverage_percentage = (administered_count / total_patients) * 100
        else:
            coverage_percentage = 0
            
        vaccine_coverage[vaccine.name] = {
            'administered_count': administered_count,
            'coverage_percentage': coverage_percentage,
            'vaccine': vaccine
        }
    
    context = {
        'total_vaccinations': total_vaccinations,
        'vaccine_coverage': vaccine_coverage,
        'total_patients': Patient.objects.filter(user=request.user).count(),
    }
    return render(request, 'coverage_analytics.html', context)

# =============================================
# AUTHENTICATION PAGES - NO LOGIN REQUIRED
# =============================================

def signup_view(request):
    """User registration page - no login required"""
    # Redirect to home if already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in!')
        return redirect('index')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome to HealthCoach, {user.username}!')
            return redirect('index')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    """User login page - no login required"""
    # Redirect to home if already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in!')
        return redirect('index')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                
                # Get the 'next' parameter if it exists (for redirect after login)
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    response = render(request, 'login.html', {'form': form})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def logout_view(request):
    """User logout - completely ends session"""
    if request.user.is_authenticated:
        username = request.user.username
        # Clear the session completely
        request.session.flush()
        logout(request)
        messages.success(request, f'You have been logged out successfully. Goodbye, {username}!')
    else:
        messages.info(request, 'You were not logged in.')
    
    response = redirect('login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response