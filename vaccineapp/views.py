from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from .models import UserProfile, Patient, Vaccine, VaccinationRecord, Appointment

# =============================================
# PROTECTED PAGES - REQUIRE LOGIN
# =============================================

@login_required(login_url='/login/')
def index(request):
    """Home page - requires login"""
    return render(request, 'index.html')

@login_required(login_url='/login/')
def about(request):
    """About page - requires login"""
    return render(request, 'about.html')

@login_required(login_url='/login/')
def contact(request):
    """Contact page - requires login"""
    return render(request, 'contact.html')

@login_required(login_url='/login/')
def service(request):
    """Services page - requires login"""
    return render(request, 'service.html')

@login_required(login_url='/login/')
def vaccine(request):
    """Vaccine information page - requires login"""
    # Get all vaccines from database
    vaccines = Vaccine.objects.filter(is_active=True)
    return render(request, 'vaccine.html', {'vaccines': vaccines})

# In views.py - make sure you have this
@login_required(login_url='/login/')
def dashboard(request):
    # Your existing dashboard code
    user = request.user
    patients_count = Patient.objects.filter(user=user).count()
    appointments_count = Appointment.objects.filter(patient__user=user, status='scheduled').count()
    vaccination_records_count = VaccinationRecord.objects.filter(patient__user=user).count()
    
    recent_appointments = Appointment.objects.filter(
        patient__user=user, 
        status='scheduled'
    ).order_by('scheduled_date')[:5]
    
    context = {
        'patients_count': patients_count,
        'appointments_count': appointments_count,
        'vaccination_records_count': vaccination_records_count,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='/login/')
def profile_view(request):
    """User profile page - requires login"""
    # Get user profile and related data
    user = request.user
    profile = UserProfile.objects.get(user=user)
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
    return render(request, 'profile.html', context)

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
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """User logout - requires login but handles gracefully"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'You have been logged out successfully. Goodbye, {username}!')
    else:
        messages.info(request, 'You were not logged in.')
    
    return redirect('login')