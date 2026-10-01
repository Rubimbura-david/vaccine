from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, date, datetime
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Count, Q
from .forms import VaccinationScheduleForm
from .models import VaccinationSchedule
from .models import Notification, Patient
from django.http import JsonResponse
from .models import VaccinationSchedule, Notification, Patient, Vaccine
from datetime import datetime
from .models import Patient, Vaccine, VaccinationRecord
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import get_language, activate
import os

# =============================================
# YOUR EXISTING IMPORTS - KEPT EXACTLY AS THEY WERE
# =============================================
from .forms import CustomUserCreationForm, VaccineInventoryForm
from .models import (
    UserProfile, Patient, Vaccine, VaccinationRecord,
    Appointment, VaccineInventory, Recommendation,
    MonitoringSession, SensorReading, SymptomReport, Symptom,
    RiskAssessment, Alert, ClinicalResponse, Outcome,
)
from .forms import RecommendationForm
from .forms import CustomUserCreationForm, VaccineInventoryForm
from .forms import RecommendationForm

# Additional forms (VaxGuard keeps only these)
from .forms import AppointmentForm, VaccinationRecordForm
# =============================================
# LOGGING CONFIGURATION
# =============================================

logger = logging.getLogger(__name__)

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
# YOUR EXISTING PROTECTED PAGES - KEPT EXACTLY AS THEY WERE
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
    try:
        print("\n" + "="*60)
        print("DASHBOARD VIEW CALLED")
        print("="*60)
        
        user = request.user
        print(f"User: {user.username} (ID: {user.id})")
        print(f"Is staff: {user.is_staff}, Is superuser: {user.is_superuser}")
        
        # Initialize all variables with default values
        notifications = []
        total_notifications = 0
        unread_count = 0
        patients_list = []
        patients_count = 0
        appointments_count = 0
        vaccination_records_count = 0
        recent_appointments = []
        vaccine_inventory = []
        total_vaccines = 0
        total_doses = 0
        low_stock_count = 0
        vaccine_types = 0
        total_administered = 0
        todays_vaccinations = 0
        vaccinations_due = 0
        overdue_vaccinations = 0
        total_patients = 0
        patients_vaccinated = 0
        vaccine_coverage = 0
        recent_vaccinations = []
        todays_schedule = []
        age_distribution = {'0-1': 0, '1-3': 0, '3-6': 0, '6-12': 0, '12-18': 0}
        vaccine_type_stats = {}
        recommendations = []
        total_recommendations = 0
        pending_count = 0
        approved_count = 0
        rejected_count = 0
        implemented_count = 0
        filter_type = request.GET.get('filter', 'all')
        fully_immunized = 0
        due_for_vaccination = 0
        overdue_vaccinations_count = 0
        total_patients_count = 0
        
        # ============ GET FILTER PARAMETER FOR VACCINATION RECORDS ============
        filter_period = request.GET.get('records_filter', 'all')  # all, today, week, month
        print(f"\n--- Filter period for records: {filter_period} ---")
        
        # ============ CALCULATE DATE RANGE BASED ON FILTER ============
        today = timezone.now().date()
        
        if filter_period == 'today':
            start_date = today
            end_date = today
        elif filter_period == 'week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif filter_period == 'month':
            start_date = today - timedelta(days=30)
            end_date = today
        else:  # 'all' or any other value
            start_date = None
            end_date = None
        
        # ============ PEDIATRIC PATIENTS (UNDER 18 YEARS) ============
        print("\n--- Calculating pediatric patients ---")
        try:
            from datetime import date
            today_date = date.today()
            
            # Calculate age in years
            def calculate_age(birth_date):
                if birth_date:
                    return today_date.year - birth_date.year - ((today_date.month, today_date.day) < (birth_date.month, birth_date.day))
                return 0
            
            # Get all patients and filter those under 18
            all_patients = Patient.objects.all()
            pediatric_patients = []
            
            for patient in all_patients:
                if patient.date_of_birth:
                    age = calculate_age(patient.date_of_birth)
                    if age < 18:
                        pediatric_patients.append(patient)
            
            pediatric_count = len(pediatric_patients)
            
            # Calculate percentage change from previous month
            
            last_month = today_date - timedelta(days=30)
            previous_month_patients = []
            
            for patient in all_patients:
                if patient.date_of_birth and patient.created_at:
                    age_last_month = calculate_age(patient.date_of_birth)
                    if age_last_month < 18 and patient.created_at.date() <= last_month:
                        previous_month_patients.append(patient)
            
            previous_count = len(previous_month_patients)
            
            if previous_count > 0:
                pediatric_change = ((pediatric_count - previous_count) / previous_count) * 100
            else:
                pediatric_change = 0
            
            pediatric_change_percent = abs(round(pediatric_change, 1))
            pediatric_trend = 'up' if pediatric_change > 0 else 'down' if pediatric_change < 0 else 'stable'
            
            # Age breakdown
            age_breakdown = {
                'neonate': 0,      # 0-28 days
                'infant': 0,       # 29 days - 12 months
                'toddler': 0,      # 1-3 years
                'preschool': 0,    # 3-5 years
                'school_age': 0,   # 5-12 years
                'adolescent': 0,   # 12-18 years
            }
            
            for patient in pediatric_patients:
                if patient.date_of_birth:
                    age = calculate_age(patient.date_of_birth)
                    age_days = (today_date - patient.date_of_birth).days
                    
                    if age_days <= 28:
                        age_breakdown['neonate'] += 1
                    elif age < 1:
                        age_breakdown['infant'] += 1
                    elif age < 3:
                        age_breakdown['toddler'] += 1
                    elif age < 5:
                        age_breakdown['preschool'] += 1
                    elif age < 12:
                        age_breakdown['school_age'] += 1
                    else:
                        age_breakdown['adolescent'] += 1
            
            print(f"Pediatric patients: {pediatric_count}, Change: {pediatric_change}%")
            
        except Exception as e:
            print(f"Error calculating pediatric patients: {e}")
            pediatric_count = 0
            pediatric_change_percent = 0
            pediatric_trend = 'stable'
            age_breakdown = {}
        
        # ============ TODAY'S VACCINATIONS ============
        print("\n--- Calculating today's vaccinations ---")
        try:
            today = timezone.now().date()
            
            # Vaccinations scheduled for today
            todays_scheduled = VaccinationRecord.objects.filter(
                date_administered=today,
                status='scheduled'
            ).count()
            
            # Vaccinations administered today
            todays_administered = VaccinationRecord.objects.filter(
                date_administered=today,
                status='administered'
            ).count()
            
            # Total for today (scheduled + administered)
            todays_total_vaccinations = todays_scheduled + todays_administered
            
            # Pending (scheduled but not yet administered)
            pending_vaccinations = todays_scheduled
            
            # Get details for tooltip
            todays_vaccinations_list = VaccinationRecord.objects.filter(
                date_administered=today
            ).select_related('patient', 'vaccine')[:10]
            
            print(f"Today's vaccinations: Total={todays_total_vaccinations}, Pending={pending_vaccinations}")
            
        except Exception as e:
            print(f"Error calculating today's vaccinations: {e}")
            todays_total_vaccinations = 0
            pending_vaccinations = 0
            todays_vaccinations_list = []
        
        # ============ VACCINATIONS DUE ============
        print("\n--- Calculating vaccinations due ---")
        try:
            today = timezone.now().date()
            
            # Vaccinations due (scheduled for today or earlier, not administered)
            due_vaccinations_count = VaccinationRecord.objects.filter(
                date_administered__lte=today,
                status='scheduled'
            ).count()
            
            # Overdue (due date < today)
            overdue_vaccinations_count_due = VaccinationRecord.objects.filter(
                date_administered__lt=today,
                status='scheduled'
            ).count()
            
            # Get details for tooltip
            due_vaccinations_list = VaccinationRecord.objects.filter(
                date_administered__lte=today,
                status='scheduled'
            ).select_related('patient', 'vaccine').order_by('date_administered')[:10]
            
            print(f"Vaccinations due: {due_vaccinations_count}, Overdue: {overdue_vaccinations_count_due}")
            
        except Exception as e:
            print(f"Error calculating vaccinations due: {e}")
            due_vaccinations_count = 0
            overdue_vaccinations_count_due = 0
            due_vaccinations_list = []
        
        # ============ VACCINE COVERAGE ============
        print("\n--- Calculating vaccine coverage ---")
        try:
            today = timezone.now().date()
            one_year_ago = today - timedelta(days=365)
            
            # Get infants aged 0-12 months
            infants = Patient.objects.filter(
                date_of_birth__gte=one_year_ago,
                date_of_birth__lte=today
            ).count()
            
            # Count infants who are fully immunized
            required_vaccines = Vaccine.objects.filter(is_active=True)
            
            fully_immunized_infants = 0
            for infant in Patient.objects.filter(date_of_birth__gte=one_year_ago, date_of_birth__lte=today):
                fully_vaccinated = True
                for vaccine in required_vaccines:
                    total_doses_required = 1  # Default
                    if hasattr(vaccine, 'doses_required'):
                        total_doses_required = vaccine.doses_required
                    
                    received_doses = VaccinationRecord.objects.filter(
                        patient=infant,
                        vaccine=vaccine,
                        status='administered'
                    ).count()
                    
                    if received_doses < total_doses_required:
                        fully_vaccinated = False
                        break
                
                if fully_vaccinated:
                    fully_immunized_infants += 1
            
            # Calculate coverage percentage
            if infants > 0:
                coverage_percentage = round((fully_immunized_infants / infants) * 100, 1)
            else:
                coverage_percentage = 0
            
            # Calculate change from previous period
            two_months_ago = today - timedelta(days=60)
            previous_infants = Patient.objects.filter(
                date_of_birth__gte=two_months_ago - timedelta(days=365),
                date_of_birth__lte=two_months_ago
            ).count()
            
            previous_fully_immunized = 0
            for infant in Patient.objects.filter(date_of_birth__gte=two_months_ago - timedelta(days=365), date_of_birth__lte=two_months_ago):
                fully_vaccinated = True
                for vaccine in required_vaccines:
                    total_doses_required = 1
                    if hasattr(vaccine, 'doses_required'):
                        total_doses_required = vaccine.doses_required
                    
                    received_doses = VaccinationRecord.objects.filter(
                        patient=infant,
                        vaccine=vaccine,
                        status='administered'
                    ).count()
                    
                    if received_doses < total_doses_required:
                        fully_vaccinated = False
                        break
                
                if fully_vaccinated:
                    previous_fully_immunized += 1
            
            if previous_infants > 0:
                previous_coverage = round((previous_fully_immunized / previous_infants) * 100, 1) if previous_fully_immunized > 0 else 0
                coverage_change = coverage_percentage - previous_coverage
            else:
                coverage_change = 0
            
            coverage_change_percent = abs(round(coverage_change, 1))
            coverage_trend = 'up' if coverage_change > 0 else 'down' if coverage_change < 0 else 'stable'
            
            # Vaccine breakdown for tooltip
            vaccine_breakdown = {}
            for vaccine in required_vaccines[:5]:
                administered = VaccinationRecord.objects.filter(
                    vaccine=vaccine,
                    status='administered'
                ).count()
                total_expected = Patient.objects.count()
                if total_expected > 0:
                    vaccine_breakdown[vaccine.name] = round((administered / total_expected) * 100, 1)
                else:
                    vaccine_breakdown[vaccine.name] = 0
            
            print(f"Vaccine coverage: {coverage_percentage}%, Change: {coverage_change}%")
            
        except Exception as e:
            print(f"Error calculating vaccine coverage: {e}")
            coverage_percentage = 0
            coverage_change_percent = 0
            coverage_trend = 'stable'
            vaccine_breakdown = {}
        
        # ============ VACCINATION STATISTICS FOR CARDS ============
        print("\n--- Fetching vaccination statistics ---")
        try:
            from django.db.models import F
            
            # All vaccinations count
            all_vaccinations = VaccinationRecord.objects.count()
            print(f"All vaccinations: {all_vaccinations}")
            
            # Complete vaccinations (dose_number equals total_doses)
            complete_vaccinations = VaccinationRecord.objects.filter(
                dose_number=F('total_doses')
            ).count()
            print(f"Complete vaccinations: {complete_vaccinations}")
            
            # Incomplete vaccinations (dose_number is less than total_doses)
            incomplete_vaccinations = VaccinationRecord.objects.filter(
                dose_number__lt=F('total_doses')
            ).count()
            print(f"Incomplete vaccinations: {incomplete_vaccinations}")
            
        except Exception as e:
            print(f"Error fetching vaccination statistics: {e}")
            all_vaccinations = 0
            complete_vaccinations = 0
            incomplete_vaccinations = 0
        
        # ============ FILTERED VACCINATION RECORDS ============
        print("\n--- Fetching filtered vaccination records ---")
        try:
            if start_date and end_date:
                recent_vaccinations = VaccinationRecord.objects.filter(
                    date_administered__gte=start_date,
                    date_administered__lte=end_date
                ).select_related('patient', 'vaccine').order_by('-date_administered')
            else:
                recent_vaccinations = VaccinationRecord.objects.all().select_related('patient', 'vaccine').order_by('-date_administered')
            
            print(f"Filtered vaccinations: {recent_vaccinations.count()}")
        except Exception as e:
            print(f"Error fetching filtered vaccinations: {e}")
            recent_vaccinations = []
        
        # ============ NOTIFICATION STATISTICS ============
        print("\n--- Fetching notification statistics ---")
        try:     
            notifications = Notification.objects.filter(
                Q(recipient=user) | Q(is_for_all=True)
            ).order_by('-created_at')[:50]
            
            total_notifications = notifications.count()
            unread_count = notifications.filter(is_read=False).count()
            print(f"Total notifications: {total_notifications}, Unread: {unread_count}")
        except Exception as e:
            print(f"Error fetching notification stats: {e}")
        
        # ============ PATIENT DATA FOR THE TABLE ============
        print("\n--- Fetching patients list ---")
        try:
            profile = getattr(user, 'userprofile', None)
            if profile and profile.user_type in ('healthcare_worker', 'admin'):
                print("HCW/Admin - fetching all patients")
                patients_list = Patient.objects.all().select_related('user').prefetch_related('vaccination_records').order_by('-created_at')[:50]
            else:
                print("Patient - fetching only their own record")
                patients_list = Patient.objects.filter(user=user).select_related('user').prefetch_related('vaccination_records').order_by('-created_at')[:50]
            print(f"Found {len(patients_list)} patients")
        except Exception as e:
            print(f"ERROR fetching patients list: {e}")
        
        # ============ PATIENT STATISTICS ============
        print("\n--- Calculating patient statistics ---")
        try:
            total_patients_count = Patient.objects.count()
            print(f"Total patients: {total_patients_count}")
            
            fully_immunized = Patient.objects.filter(
                vaccination_records__status='administered'
            ).distinct().count()
            print(f"Fully immunized: {fully_immunized}")
            
            today = timezone.now().date()
            print(f"Today's date: {today}")
            
            due_for_vaccination = Patient.objects.filter(
                vaccination_records__status='scheduled',
                vaccination_records__date_administered__gte=today
            ).distinct().count()
            print(f"Due for vaccination: {due_for_vaccination}")
            
            overdue_vaccinations_count = Patient.objects.filter(
                vaccination_records__status='scheduled',
                vaccination_records__date_administered__lt=today
            ).distinct().count()
            print(f"Overdue vaccinations: {overdue_vaccinations_count}")
            
        except Exception as e:
            print(f"ERROR calculating patient stats: {e}")
        
        # ============ REST OF YOUR EXISTING CODE ============
        print("\n--- Fetching other dashboard data ---")
        
        # Patient statistics
        try:
            patients_count = Patient.objects.filter(user=user).count()
            print(f"User's patients: {patients_count}")
        except Exception as e:
            print(f"Error in patients_count: {e}")
            
        try:
            appointments_count = Appointment.objects.filter(patient__user=user, status='scheduled').count()
            print(f"User's appointments: {appointments_count}")
        except Exception as e:
            print(f"Error in appointments_count: {e}")
            
        try:
            vaccination_records_count = VaccinationRecord.objects.filter(patient__user=user).count()
            print(f"User's vaccination records: {vaccination_records_count}")
        except Exception as e:
            print(f"Error in vaccination_records_count: {e}")
        
        # Recent appointments
        try:
            recent_appointments = Appointment.objects.filter(
                patient__user=user, 
                status='scheduled'
            ).order_by('scheduled_date')[:5]
            print(f"Recent appointments: {recent_appointments.count()}")
        except Exception as e:
            print(f"Error in recent_appointments: {e}")
        
        # Vaccine inventory data
        try:
            vaccine_inventory = VaccineInventory.objects.select_related('vaccine').all()
            print(f"Vaccine inventory items: {vaccine_inventory.count()}")
        except Exception as e:
            print(f"Error in vaccine_inventory: {e}")
        
        # Calculate vaccine statistics
        total_vaccines = len(vaccine_inventory) if vaccine_inventory else 0
        
        try:
            total_doses = sum(item.current_stock for item in vaccine_inventory if item and hasattr(item, 'current_stock'))
        except Exception as e:
            print(f"Error calculating total_doses: {e}")
        
        try:
            low_stock_count = sum(1 for item in vaccine_inventory if item and hasattr(item, 'status') and item.status in ['low_stock', 'critical'])
        except Exception as e:
            print(f"Error calculating low_stock_count: {e}")
        
        try:
            vaccine_types = len(set(item.vaccine.vaccine_type for item in vaccine_inventory if item and item.vaccine and hasattr(item.vaccine, 'vaccine_type')))
        except Exception as e:
            print(f"Error calculating vaccine_types: {e}")
        
        # Total administered vaccines (last 30 days)
        try:
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            total_administered = VaccinationRecord.objects.filter(
                status='administered',
                date_administered__gte=thirty_days_ago
            ).count()
            print(f"Total administered (30 days): {total_administered}")
        except Exception as e:
            print(f"Error in total_administered: {e}")
        
        # Additional dashboard statistics
        today = timezone.now().date()
        
        try:
            todays_vaccinations = VaccinationRecord.objects.filter(
                date_administered=today,
                status='administered'
            ).count()
            print(f"Today's vaccinations: {todays_vaccinations}")
        except Exception as e:
            print(f"Error in todays_vaccinations: {e}")
        
        try:
            vaccinations_due = VaccinationRecord.objects.filter(
                date_administered=today,
                status='scheduled'
            ).count()
            print(f"Vaccinations due: {vaccinations_due}")
        except Exception as e:
            print(f"Error in vaccinations_due: {e}")
        
        try:
            overdue_vaccinations = VaccinationRecord.objects.filter(
                date_administered__lt=today,
                status='scheduled'
            ).count()
            print(f"Overdue vaccinations: {overdue_vaccinations}")
        except Exception as e:
            print(f"Error in overdue_vaccinations: {e}")
        
        # Vaccine coverage percentage
        try:
            total_patients = Patient.objects.count()
            patients_vaccinated = Patient.objects.filter(
                vaccination_records__status='administered'
            ).distinct().count()
            
            if total_patients > 0:
                vaccine_coverage = (patients_vaccinated / total_patients) * 100
            else:
                vaccine_coverage = 0
            print(f"Vaccine coverage: {vaccine_coverage}%")
        except Exception as e:
            print(f"Error in vaccine_coverage: {e}")
        
        # Today's schedule
        try:
            todays_schedule = Appointment.objects.filter(
                scheduled_date__date=today,
                status__in=['scheduled', 'confirmed']
            ).select_related('patient').order_by('scheduled_date')
            print(f"Today's schedule: {todays_schedule.count()}")
        except Exception as e:
            print(f"Error in todays_schedule: {e}")
        
        # Age distribution data
        try:
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
            print(f"Age distribution: {age_distribution}")
        except Exception as e:
            print(f"Error in age_distribution: {e}")
        
        # Vaccine type distribution
        try:
            for vaccine_type, display_name in Vaccine.VACCINE_TYPE_CHOICES:
                count = Vaccine.objects.filter(vaccine_type=vaccine_type, is_active=True).count()
                vaccine_type_stats[vaccine_type] = {
                    'count': count,
                    'display_name': display_name
                }
            print(f"Vaccine type stats: {vaccine_type_stats}")
        except Exception as e:
            print(f"Error in vaccine_type_stats: {e}")
        
        # Recommendations data
        try:
            filter_type = request.GET.get('filter', 'all')
            recommendations_queryset = Recommendation.objects.all().order_by('-created_at')
            
            if filter_type == 'pending':
                recommendations = recommendations_queryset.filter(status='pending')
            elif filter_type == 'approved':
                recommendations = recommendations_queryset.filter(status='approved')
            elif filter_type == 'rejected':
                recommendations = recommendations_queryset.filter(status='rejected')
            elif filter_type == 'implemented':
                recommendations = recommendations_queryset.filter(status='implemented')
            else:  
                recommendations = recommendations_queryset
            
            total_recommendations = recommendations_queryset.count()
            pending_count = recommendations_queryset.filter(status='pending').count()
            approved_count = recommendations_queryset.filter(status='approved').count()
            rejected_count = recommendations_queryset.filter(status='rejected').count()
            implemented_count = recommendations_queryset.filter(status='implemented').count()
            
            print(f"Recommendations: total={total_recommendations}, pending={pending_count}, approved={approved_count}")
            
        except Exception as e:
            print(f"Error in recommendations: {e}")
        
        # Build context with all data
        context = {
            # Filter parameter for records
            'records_filter': filter_period,
            
            # New statistics cards data
            'pediatric_count': pediatric_count,
            'pediatric_change_percent': pediatric_change_percent,
            'pediatric_trend': pediatric_trend,
            'age_breakdown': age_breakdown,
            'todays_total_vaccinations': todays_total_vaccinations,
            'pending_vaccinations': pending_vaccinations,
            'todays_vaccinations_list': todays_vaccinations_list,
            'due_vaccinations_count': due_vaccinations_count,
            'overdue_vaccinations_count_due': overdue_vaccinations_count_due,
            'due_vaccinations_list': due_vaccinations_list,
            'coverage_percentage': coverage_percentage,
            'coverage_change_percent': coverage_change_percent,
            'coverage_trend': coverage_trend,
            'vaccine_breakdown': vaccine_breakdown,
            
            # Vaccination statistics for cards
            'all_vaccinations': all_vaccinations,
            'complete_vaccinations': complete_vaccinations,
            'incomplete_vaccinations': incomplete_vaccinations,
            
            # Filtered vaccination records
            'recent_vaccinations': recent_vaccinations,
            
            # Patient data for the table
            'patients': patients_list,
            'patients_list': patients_list,
            'fully_immunized': fully_immunized,
            'due_for_vaccination': due_for_vaccination,
            'overdue_vaccinations_count': overdue_vaccinations_count,
            'total_patients_count': total_patients_count,
            
            # Original patient stats
            'patients_count': patients_count,
            'appointments_count': appointments_count,
            'vaccination_records_count': vaccination_records_count,
            'recent_appointments': recent_appointments,
            
            # Vaccine inventory data
            'vaccine_inventory': vaccine_inventory,
            'total_vaccines': total_vaccines,
            'total_doses': total_doses,
            'low_stock_count': low_stock_count,
            'vaccine_types': vaccine_types,
            'total_administered': total_administered,
            
            # Today's stats
            'todays_vaccinations': todays_vaccinations,
            'vaccinations_due': vaccinations_due,
            'overdue_vaccinations': overdue_vaccinations,
            'vaccine_coverage': round(vaccine_coverage, 1) if vaccine_coverage else 0,
            'todays_schedule': todays_schedule,
            'age_distribution': age_distribution,
            'vaccine_type_stats': vaccine_type_stats,
            
            # Total patients stats (for coverage)
            'total_patients': total_patients,
            'patients_vaccinated': patients_vaccinated,
            
            # Recommendations data
            'recommendations': recommendations,
            'total_recommendations': total_recommendations,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'implemented_count': implemented_count,
            'current_filter': filter_type,
            'user_status': user.userprofile.user_type if hasattr(user, 'userprofile') else 'parent',
            
            # Notification data
            'notifications': notifications,
            'total_notifications': total_notifications,
            'unread_count': unread_count,
        }
        
        print("\n" + "="*60)
        print("✅ DASHBOARD VIEW COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
        response = render(request, 'dashboard.html', context)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
        
    except Exception as e:
        print("\n" + "!"*60)
        print("❌ ERROR IN DASHBOARD VIEW:")
        import traceback
        traceback.print_exc()
        print("!"*60 + "\n")
        
        # Return minimal context with all required variables
        context = {
            'error_message': str(e),
            'error_details': traceback.format_exc() if settings.DEBUG else None,
            
            # Filter defaults
            'records_filter': 'all',
            
            # New statistics defaults
            'pediatric_count': 0,
            'pediatric_change_percent': 0,
            'pediatric_trend': 'stable',
            'age_breakdown': {},
            'todays_total_vaccinations': 0,
            'pending_vaccinations': 0,
            'todays_vaccinations_list': [],
            'due_vaccinations_count': 0,
            'overdue_vaccinations_count_due': 0,
            'due_vaccinations_list': [],
            'coverage_percentage': 0,
            'coverage_change_percent': 0,
            'coverage_trend': 'stable',
            'vaccine_breakdown': {},
            
            # Vaccination statistics defaults
            'all_vaccinations': 0,
            'complete_vaccinations': 0,
            'incomplete_vaccinations': 0,
            
            # Filtered records defaults
            'recent_vaccinations': [],
            
            # Patient data defaults
            'patients_list': [],
            'fully_immunized': 0,
            'due_for_vaccination': 0,
            'overdue_vaccinations_count': 0,
            'total_patients_count': 0,
            
            # Original defaults
            'patients_count': 0,
            'appointments_count': 0,
            'vaccination_records_count': 0,
            'recent_appointments': [],
            'vaccine_inventory': [],
            'total_vaccines': 0,
            'total_doses': 0,
            'low_stock_count': 0,
            'vaccine_types': 0,
            'total_administered': 0,
            'todays_vaccinations': 0,
            'vaccinations_due': 0,
            'overdue_vaccinations': 0,
            'vaccine_coverage': 0,
            'todays_schedule': [],
            'age_distribution': {'0-1': 0, '1-3': 0, '3-6': 0, '6-12': 0, '12-18': 0},
            'vaccine_type_stats': {},
            'total_patients': 0,
            'patients_vaccinated': 0,
            'recommendations': [],
            'total_recommendations': 0,
            'pending_count': 0,
            'approved_count': 0,
            'rejected_count': 0,
            'implemented_count': 0,
            'current_filter': 'all',
            
            # Notification defaults
            'notifications': [],
            'total_notifications': 0,
            'unread_count': 0,
        }
        return render(request, 'dashboard_error.html', context)

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
# YOUR EXISTING VACCINE INVENTORY MANAGEMENT
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
    from datetime import datetime as dt

    try:
        data = json.loads(request.body)
        
        # Handle age groups (convert from list to comma-separated string)
        age_groups = data.get('ageGroups', [])
        if isinstance(age_groups, list):
            age_groups_str = ','.join(age_groups)
        else:
            age_groups_str = age_groups

        # Convert date string to date object
        expiry_date_str = data.get('expiryDate')
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = dt.strptime(expiry_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid expiry date format: {expiry_date_str}. Use YYYY-MM-DD.'
                }, status=400)
        
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
                 doses_required=int(data.get('totalDosesRequired', 1)) or 1,
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
            expiration_date=expiry_date,
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
# YOUR EXISTING VACCINE API ENDPOINTS
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
            'doses_required': vaccine.vaccine.doses_required if vaccine.vaccine else 1,
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
    import traceback

    # Guard: reject invalid IDs early
    if not vaccine_id or vaccine_id == 'null':
        return JsonResponse({
            'success': False,
            'message': 'Invalid vaccine ID. The delete request did not include a valid vaccine.'
        }, status=400)

    try:
        vaccine = VaccineInventory.objects.get(id=vaccine_id)
        vaccine_name = vaccine.get_display_name()
        vaccine.delete()

        return JsonResponse({
            'success': True,
            'message': f'Vaccine {vaccine_name} deleted successfully'
        })

    except VaccineInventory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Vaccine not found'
        }, status=404)
    except Exception as e:
        print("DELETE VACCINE ERROR:", e)
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
@login_required(login_url='/login/')
def update_vaccine_api(request, vaccine_id):
    """API endpoint to update a vaccine"""
    from datetime import datetime as dt
    import traceback

    try:
        vaccine = VaccineInventory.objects.get(id=vaccine_id)
        data = json.loads(request.body)

        # Update simple fields
        if 'current_stock' in data and data['current_stock'] not in (None, ''):
            vaccine.current_stock = int(data['current_stock'])
        if 'min_stock_level' in data and data['min_stock_level'] not in (None, ''):
            vaccine.min_stock_level = int(data['min_stock_level'])
        # Total doses required lives on the Vaccine model, not the Inventory row
        if 'doses_required' in data and data['doses_required'] not in (None, ''):
            if vaccine.vaccine:
                vaccine.vaccine.doses_required = int(data['doses_required']) or 1
                vaccine.vaccine.save()
        if 'storage_temperature' in data:
            vaccine.storage_temperature = data['storage_temperature']
        if 'description' in data:
            vaccine.description = data['description']
        if 'lot_number' in data:
            vaccine.lot_number = data['lot_number']
        if 'manufacturer' in data:
            vaccine.manufacturer = data['manufacturer']
        if 'target_diseases' in data:
            vaccine.target_diseases = data['target_diseases']

        # Convert expiration_date string → date object
        if 'expiration_date' in data and data['expiration_date']:
            try:
                vaccine.expiration_date = dt.strptime(
                    data['expiration_date'], '%Y-%m-%d'
                ).date()
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'message': f"Invalid expiry date: {data['expiration_date']}"
                }, status=400)

        vaccine.save()

        return JsonResponse({
            'success': True,
            'message': f'Vaccine {vaccine.get_display_name()} updated successfully'
        })

    except VaccineInventory.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Vaccine not found'}, status=404)
    except Exception as e:
        print("UPDATE VACCINE ERROR:", e)
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# =============================================
# YOUR EXISTING PATIENT MANAGEMENT
# =============================================

@login_required(login_url='/login/')
@no_cache_after_logout
def patient_list(request):
    """List patients — HCW/Admin see all; patients see only their own."""
    profile = getattr(request.user, 'userprofile', None)

    if profile and profile.user_type in ('healthcare_worker', 'admin'):
        patients = Patient.objects.all().select_related('user')
    else:
        patients = Patient.objects.filter(user=request.user).select_related('user')

    total_patients = patients.count()
    patients_with_complete_vaccinations = sum(
        1 for patient in patients
        if patient.vaccination_records.filter(status='administered').exists()
    )

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
# YOUR EXISTING AUTHENTICATION PAGES
# =============================================

def signup_view(request):
    """
    Enhanced user registration page with logging and welcome email functionality
    """
    # Redirect to home if already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in!')
        return redirect('index')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            try:
                # Save the user
                user = form.save()
                
                # Log the successful registration
                logger.info(f"New user registered: {user.username} ({user.email})")
                
                # Log the user in
                login(request, user)
                
                # Send welcome email (optional - won't fail if email not configured)
                try:
                    send_welcome_email(user)
                except Exception as e:
                    logger.warning(f"Failed to send welcome email to {user.email}: {str(e)}")
                
                # Success message with personal touch
                messages.success(
                    request, 
                    f'🎉 Welcome to HealthCoach, {user.first_name or user.username}! '
                    f'Your account has been created successfully. '
                    f'You can now manage your family\'s vaccinations.'
                )
                
                # Redirect to dashboard for better user experience
                return redirect('dashboard')
                
            except Exception as e:
                logger.error(f"Error during user registration: {str(e)}")
                messages.error(
                    request, 
                    'An error occurred during registration. Please try again.'
                )
                return render(request, 'signup.html', {'form': form})
                
        else:
            # Form is invalid - collect and display errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
                    messages.error(request, f"{field.title()}: {error}")
            
            # Log validation errors
            logger.warning(f"Signup form validation failed: {', '.join(error_messages)}")
            
            # Display user-friendly error message
            messages.error(
                request, 
                'Please correct the errors below and try again.'
            )
    
    else:
        form = CustomUserCreationForm()
    
    # Pass the form to template
    context = {
        'form': form,
        'page_title': 'Create Account - HealthCoach',
    }
    
    return render(request, 'signup.html', context)


def send_welcome_email(user):
    """
    Send welcome email to newly registered users
    This function is optional - it won't break if email is not configured
    """
    subject = 'Welcome to HealthCoach - Your Vaccination Partner'
    
    # HTML email content
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ padding: 30px 20px; background: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #4caf50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            .button:hover {{ background: #45a049; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            ul {{ list-style-type: none; padding: 0; }}
            ul li {{ margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to HealthCoach! 🎉</h1>
            </div>
            <div class="content">
                <h2>Hello {user.first_name or user.username}!</h2>
                <p>Thank you for joining HealthCoach. We're excited to help you manage your family's vaccination journey.</p>
                
                <h3>✨ What you can do now:</h3>
                <ul>
                    <li>✅ Add family members to manage their vaccinations</li>
                    <li>✅ View and schedule vaccination appointments</li>
                    <li>✅ Track vaccination records and history</li>
                    <li>✅ Get reminders for upcoming vaccinations</li>
                    <li>✅ Access vaccine information and resources</li>
                </ul>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="http://127.0.0.1:8000/dashboard/" class="button">Go to Your Dashboard</a>
                </p>
                
                <p>If you have any questions, feel free to contact our support team at support@healthcoach.com.</p>
                
                <p>Best regards,<br>The HealthCoach Team</p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} HealthCoach. All rights reserved.</p>
                <p>This email was sent to {user.email}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text alternative
    plain_message = f"""
    Welcome to HealthCoach, {user.first_name or user.username}!
    
    Thank you for joining HealthCoach. We're excited to help you manage your family's vaccination journey.
    
    What you can do now:
    - Add family members to manage their vaccinations
    - View and schedule vaccination appointments
    - Track vaccination records and history
    - Get reminders for upcoming vaccinations
    - Access vaccine information and resources
    
    Visit your dashboard: http://127.0.0.1:8000/dashboard/
    
    Best regards,
    The HealthCoach Team
    """
    
    # Send email (won't fail if email settings not configured)
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,  # Don't raise exception if email fails
        )
    except Exception as e:
        logger.warning(f"Failed to send welcome email: {str(e)}")


# =============================================
# YOUR EXISTING AJAX ENDPOINTS
# =============================================

def check_username_availability(request):
    """
    AJAX endpoint to check if username is available
    """
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        username = request.GET.get('username', '')
        
        if len(username) < 3:
            return JsonResponse({
                'available': False,
                'message': 'Username must be at least 3 characters long'
            })
        
        if not username.isalnum() and '_' not in username:
            return JsonResponse({
                'available': False,
                'message': 'Username can only contain letters, numbers, and underscores'
            })
        
        exists = User.objects.filter(username=username).exists()
        
        if exists:
            return JsonResponse({
                'available': False,
                'message': 'Username is already taken'
            })
        else:
            return JsonResponse({
                'available': True,
                'message': 'Username is available'
            })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def check_email_availability(request):
    """
    AJAX endpoint to check if email is already registered
    """
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        email = request.GET.get('email', '')
        
        if not email:
            return JsonResponse({'available': False, 'message': 'Email is required'})
        
        exists = User.objects.filter(email=email).exists()
        
        if exists:
            return JsonResponse({
                'available': False,
                'message': 'Email is already registered'
            })
        else:
            return JsonResponse({
                'available': True,
                'message': 'Email is available'
            })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


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
                next_url = request.GET.get('next', 'dashboard')
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


@login_required
def create_recommendation(request):
    """
    View to create a new recommendation
    """
    if request.method == 'POST':
        form = RecommendationForm(request.POST, request.FILES)
        if form.is_valid():
            recommendation = form.save(commit=False)
            recommendation.created_by = request.user
            recommendation.save()
            messages.success(request, 'Recommendation created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RecommendationForm()
    
    # Get data for dropdowns
    vaccines = Vaccine.objects.filter(is_active=True)
    inventory_items = VaccineInventory.objects.all()
    
    context = {
        'form': form,
        'vaccines': vaccines,
        'inventory_items': inventory_items,
    }
    return render(request, 'recommendation_form.html', context)


@csrf_exempt
def update_recommendation_status(request, recommendation_id):
    """API endpoint to update recommendation status and handle inventory"""
    print(f"\n{'='*60}")
    print(f"🔵 UPDATE RECOMMENDATION STATUS CALLED")
    print(f"📝 Recommendation ID: {recommendation_id}")
    print(f"🔧 Method: {request.method}")
    print(f"📦 Request body: {request.body}")
    print(f"{'='*60}\n")
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Parse request data
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            print(f"✅ Parsed JSON data: {data}")
            print(f"🎯 New status: {new_status}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Invalid JSON data: {str(e)}'
            }, status=400)
        
        if not new_status:
            print("❌ No status provided")
            return JsonResponse({
                'success': False,
                'message': 'Status is required'
            }, status=400)
        
        # Get the recommendation
        try:
            recommendation = Recommendation.objects.get(id=recommendation_id)
            print(f"✅ Found recommendation: '{recommendation.title}'")
            print(f"   Current status: {recommendation.status}")
            print(f"   Recommended quantity: {recommendation.recommended_quantity}")
        except Recommendation.DoesNotExist:
            print(f"❌ Recommendation {recommendation_id} not found")
            return JsonResponse({
                'success': False,
                'message': 'Recommendation not found'
            }, status=404)
        
        # If status is being changed to 'implemented', update inventory
        inventory_message = ""
        if new_status == 'implemented' and recommendation.status != 'implemented':
            print("\n🔄 Processing inventory update...")
            
            try:
                # Get recommendation details
                vaccine_name = recommendation.title
                if recommendation.vaccine and recommendation.vaccine.name:
                    vaccine_name = recommendation.vaccine.name
                
                quantity = recommendation.recommended_quantity or 1
                print(f"💉 Vaccine: '{vaccine_name}', Quantity: {quantity}")
                
                # Check if vaccine already exists in inventory
                print("🔍 Searching for existing inventory...")
                inventory_item = None
                
                # Try searching by vaccine relation
                if recommendation.vaccine:
                    inventory_item = VaccineInventory.objects.filter(
                        vaccine=recommendation.vaccine
                    ).first()
                    if inventory_item:
                        print(f"✅ Found by vaccine relation: ID {inventory_item.id}")
                
                # Try searching by vaccine name
                if not inventory_item:
                    inventory_item = VaccineInventory.objects.filter(
                        vaccine_name__icontains=vaccine_name
                    ).first()
                    if inventory_item:
                        print(f"✅ Found by vaccine_name field: ID {inventory_item.id}")
                
                # Try searching through vaccine model
                if not inventory_item:
                    matching_vaccine = Vaccine.objects.filter(name__icontains=vaccine_name).first()
                    if matching_vaccine:
                        inventory_item = VaccineInventory.objects.filter(
                            vaccine=matching_vaccine
                        ).first()
                        if inventory_item:
                            print(f"✅ Found through Vaccine model: ID {inventory_item.id}")
                
                if inventory_item:
                    # Vaccine exists - add to current stock
                    print(f"📊 Current stock: {inventory_item.current_stock}")
                    old_stock = inventory_item.current_stock
                    inventory_item.current_stock += quantity
                    inventory_item.save()
                    
                    # Add note about this addition
                    notes = inventory_item.notes or ''
                    inventory_item.notes = notes + f"\n[{timezone.now().date()}] Added {quantity} doses from recommendation #{recommendation_id}"
                    inventory_item.save(update_fields=['notes'])
                    
                    inventory_message = f"Added {quantity} doses to existing inventory. Previous: {old_stock}, New: {inventory_item.current_stock}"
                    print(f"✅ {inventory_message}")
                    
                else:
                    # Create new vaccine inventory item
                    print("➕ Creating new inventory item...")
                    
                    # Get manufacturer from vaccine if available
                    manufacturer = 'From Recommendation'
                    if recommendation.vaccine and recommendation.vaccine.manufacturer:
                        manufacturer = recommendation.vaccine.manufacturer
                    
                    new_inventory = VaccineInventory.objects.create(
                        vaccine_name=vaccine_name,
                        vaccine_type='other',
                        current_stock=quantity,
                        min_stock_level=10,
                        doses_per_vial=1,
                        lot_number=f"IMP-{timezone.now().strftime('%Y%m%d')}-{recommendation_id}",
                        expiration_date=timezone.now().date() + timezone.timedelta(days=365),
                        manufacturer=manufacturer,
                        storage_temperature='2°C to 8°C',
                        description=recommendation.description,
                        notes=f"Created from recommendation #{recommendation_id} on {timezone.now().date()}",
                        status='in_stock'
                    )
                    
                    # Link to vaccine if possible
                    existing_vaccine = Vaccine.objects.filter(name__icontains=vaccine_name).first()
                    if existing_vaccine:
                        new_inventory.vaccine = existing_vaccine
                        new_inventory.vaccine_type = existing_vaccine.vaccine_type
                        new_inventory.save()
                        print(f"✅ Linked to existing vaccine: {existing_vaccine.name}")
                    
                    inventory_message = f"Created new inventory item '{vaccine_name}' with {quantity} doses"
                    print(f"✅ {inventory_message}")
                    
            except Exception as inventory_error:
                print(f"❌ INVENTORY ERROR: {inventory_error}")
                import traceback
                traceback.print_exc()
                inventory_message = f"Inventory update failed: {str(inventory_error)}"
        
        # Update the recommendation status
        print(f"\n🔄 Updating recommendation status from '{recommendation.status}' to '{new_status}'")
        old_status = recommendation.status
        recommendation.status = new_status
        
        # Add review information
        if new_status in ['approved', 'rejected', 'implemented']:
            recommendation.reviewed_by = request.user if request.user.is_authenticated else None
            recommendation.review_date = timezone.now()
        
        recommendation.save()
        print(f"✅ Status updated successfully")
        
        # Prepare response message
        if inventory_message:
            response_message = f"Recommendation marked as {new_status}. {inventory_message}"
        else:
            response_message = f'Recommendation status updated from {old_status} to {new_status}'
        
        print(f"\n✅ Sending success response: {response_message}")
        return JsonResponse({
            'success': True,
            'message': response_message,
            'new_status': new_status,
            'inventory_updated': new_status == 'implemented' and 'failed' not in inventory_message.lower()
        })
        
    except Exception as e:
        print(f"\n❌ UNHANDLED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def edit_recommendation(request, pk):
    """
    View to edit an existing recommendation
    """
    recommendation = get_object_or_404(Recommendation, pk=pk)
    
    if request.method == 'POST':
        form = RecommendationForm(request.POST, request.FILES, instance=recommendation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recommendation updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RecommendationForm(instance=recommendation)
    
    context = {
        'form': form,
        'recommendation': recommendation,
        'is_edit': True
    }
    return render(request, 'recommendation_form.html', context)


@login_required
def delete_recommendation(request, pk):
    """
    View to delete a recommendation
    """
    recommendation = get_object_or_404(Recommendation, pk=pk)
    
    if request.method == 'POST':
        title = recommendation.title
        recommendation.delete()
        messages.success(request, f'Recommendation "{title}" deleted successfully!')
        return redirect('dashboard')
    
    # If not POST, redirect to dashboard
    return redirect('dashboard')


@csrf_exempt
def create_recommendation_api(request):
    """API endpoint to create a new recommendation"""
    if request.method == 'POST':
        try:
            # Parse JSON data from request
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            # Get form data
            title = data.get('title')
            description = data.get('description')
            recommendation_type = data.get('recommendation_type', 'other')
            priority = data.get('priority', 'medium')
            vaccine_id = data.get('vaccine_id')
            
            # Validate required fields
            if not title or not description:
                return JsonResponse({
                    'success': False,
                    'message': 'Title and description are required'
                }, status=400)
            
            # Create the recommendation
            recommendation = Recommendation.objects.create(
                title=title,
                description=description,
                recommendation_type=recommendation_type,
                priority=priority,
                status='pending',  # Default status
                created_by=request.user if request.user.is_authenticated else None,
                vaccine_id=vaccine_id if vaccine_id else None,
                recommended_quantity=data.get('recommended_quantity'),
                estimated_cost=data.get('estimated_cost'),
                justification=data.get('justification', ''),
                benefits=data.get('benefits', ''),
                risks=data.get('risks', ''),
                suggested_date=data.get('suggested_date'),
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Recommendation created successfully',
                'id': recommendation.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def delete_recommendation_api(request, recommendation_id):
    """API endpoint to delete a recommendation"""
    if request.method == 'DELETE':
        try:
            # Get the recommendation
            recommendation = Recommendation.objects.get(id=recommendation_id)
            
            # Delete it
            recommendation.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Recommendation deleted successfully'
            })
            
        except Recommendation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Recommendation not found'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# =============================================
# YOUR COLLEAGUE'S ADDITIONAL VIEWS - ADDED BELOW
# =============================================

# =============================================
# PATIENT DASHBOARD
# =============================================

@login_required(login_url='/login/')
def patient_dashboard(request):
    """Patient dashboard - uses patient_dashboard.html"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard')
    
    try:
        # Get the patient for this user
        patient = Patient.objects.filter(user=request.user).first()
        
        if not patient:
            # Create default patient if not exists
            patient = Patient.objects.create(
                user=request.user,
                first_name=request.user.first_name or 'User',
                last_name=request.user.last_name or 'Patient',
                date_of_birth='2000-01-01',
                gender='U'
            )
        
        # Get counts and data
        today = datetime.now()
        next_week = today + timedelta(days=7)
        next_month = today + timedelta(days=30)
        
        # Upcoming appointments count
        upcoming_appointments_count = Appointment.objects.filter(
            patient=patient,
            scheduled_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).count()
        
        # Recent appointments (for display)
        recent_appointments = Appointment.objects.filter(
            patient=patient
        ).select_related('assigned_doctor', 'assigned_doctor__user').order_by('-scheduled_date')[:3]
        
        # Active prescriptions count
        recent_prescriptions_count = Prescription.objects.filter(
            patient=patient,
            status='active'
        ).count()
        
        # Recent prescriptions list
        recent_prescriptions = Prescription.objects.filter(
            patient=patient
        ).select_related('doctor', 'doctor__user').order_by('-date_issued')[:3]
        
        # Vaccination records count
        vaccination_records_count = VaccinationRecord.objects.filter(
            patient=patient
        ).count()
        
        # Upcoming vaccinations
        upcoming_vaccinations = VaccinationRecord.objects.filter(
            patient=patient,
            status='scheduled',
            next_due_date__gte=today
        ).select_related('vaccine').order_by('next_due_date')[:3]
        
        # Total consultations count
        total_consultations = Consultation.objects.filter(
            patient=patient
        ).count()
        
        # Recent consultations
        recent_consultations = Consultation.objects.filter(
            patient=patient
        ).select_related('doctor', 'doctor__user').order_by('-consultation_date')[:3]
        
        # Medical record
        medical_record = MedicalRecord.objects.filter(patient=patient).first()
        
        # Create recent activities
        recent_activities = []
        
        # Add recent appointments to activities
        for appt in Appointment.objects.filter(patient=patient).order_by('-scheduled_date')[:2]:
            recent_activities.append({
                'icon': 'fa-calendar-check',
                'icon_class': 'completed' if appt.status == 'completed' else 'pending',
                'text': f"{appt.get_appointment_type_display()} with Dr. {appt.assigned_doctor.user.get_full_name() if appt.assigned_doctor else 'Doctor'}",
                'time': appt.scheduled_date.strftime("%b %d, %Y at %I:%M %p")
            })
        
        # Add recent prescriptions to activities
        for presc in Prescription.objects.filter(patient=patient).order_by('-date_issued')[:2]:
            recent_activities.append({
                'icon': 'fa-prescription',
                'icon_class': 'info',
                'text': f"Prescription issued by Dr. {presc.doctor.user.get_full_name() if presc.doctor else 'Doctor'}",
                'time': presc.date_issued.strftime("%b %d, %Y")
            })
        
        # Add recent vaccinations to activities
        for vacc in VaccinationRecord.objects.filter(patient=patient).order_by('-date_administered')[:2]:
            recent_activities.append({
                'icon': 'fa-syringe',
                'icon_class': 'completed' if vacc.status == 'administered' else 'warning',
                'text': f"{vacc.vaccine.name} vaccination",
                'time': vacc.date_administered.strftime("%b %d, %Y") if vacc.date_administered else "Scheduled"
            })
        
        # Create notifications
        notifications = []
        if upcoming_appointments_count > 0:
            notifications.append(f"You have {upcoming_appointments_count} upcoming appointment(s)")
        if recent_prescriptions_count > 0:
            notifications.append(f"You have {recent_prescriptions_count} active prescription(s)")
        
        # Check for overdue vaccinations
        overdue_vaccinations = VaccinationRecord.objects.filter(
            patient=patient,
            status='scheduled',
            next_due_date__lt=today
        ).count()
        if overdue_vaccinations > 0:
            notifications.append(f"You have {overdue_vaccinations} overdue vaccination(s)")
        
        context = {
            'patient': patient,
            'upcoming_appointments_count': upcoming_appointments_count,
            'recent_appointments': recent_appointments,
            'recent_prescriptions_count': recent_prescriptions_count,
            'recent_prescriptions': recent_prescriptions,
            'vaccination_records_count': vaccination_records_count,
            'upcoming_vaccinations': upcoming_vaccinations,
            'total_consultations': total_consultations,
            'recent_consultations': recent_consultations,
            'medical_record': medical_record,
            'recent_activities': recent_activities[:5],  # Limit to 5 activities
            'notifications': notifications,
            'notifications_count': len(notifications),
            'today': today,
            'next_week': next_week,
            'next_month': next_month,
        }
        
    except Exception as e:
        # Log the error and provide fallback context
        print(f"Error in patient_dashboard: {str(e)}")
        context = {
            'notifications_count': 0,
            'notifications': [],
            'upcoming_appointments_count': 0,
            'recent_appointments': [],
            'recent_prescriptions_count': 0,
            'recent_prescriptions': [],
            'vaccination_records_count': 0,
            'upcoming_vaccinations': [],
            'total_consultations': 0,
            'recent_consultations': [],
            'medical_record': None,
            'recent_activities': [],
        }
    
    return render(request, 'patient_dashboard.html', context)


@login_required(login_url='/login/')
def patient_profile(request):
    """Patient profile page"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard')
    
    # Use first() instead of get() to handle multiple patients
    patient = Patient.objects.filter(user=request.user).first()
    
    if not patient:
        messages.warning(request, 'Please complete your patient profile.')
        context = {
            'patient': None,
        }
    else:
        # Get user profile
        user_profile = UserProfile.objects.filter(user=request.user).first()
        
        context = {
            'patient': patient,
            'user_profile': user_profile,
        }
    
    return render(request, 'patient_profile.html', context)


@login_required(login_url='/login/')
def update_patient_profile(request):
    """Update patient profile"""
    if request.method == 'POST':
        patient = Patient.objects.filter(user=request.user).first()
        
        if patient:
            patient.first_name = request.POST.get('first_name', patient.first_name)
            patient.last_name = request.POST.get('last_name', patient.last_name)
            patient.date_of_birth = request.POST.get('date_of_birth', patient.date_of_birth)
            patient.gender = request.POST.get('gender', patient.gender)
            patient.blood_type = request.POST.get('blood_type', patient.blood_type)
            patient.allergies = request.POST.get('allergies', patient.allergies)
            patient.medical_conditions = request.POST.get('medical_conditions', patient.medical_conditions)
            patient.current_medications = request.POST.get('current_medications', patient.current_medications)
            patient.patient_phone = request.POST.get('phone', patient.patient_phone)
            patient.patient_email = request.POST.get('email', patient.patient_email)
            patient.weight = request.POST.get('weight', patient.weight)
            patient.height = request.POST.get('height', patient.height)
            patient.save()
            
            messages.success(request, 'Profile updated successfully!')
        else:
            messages.error(request, 'Patient profile not found.')
        
        return redirect('patient_profile')
    
    return redirect('patient_profile')


# =============================================
# APPOINTMENTS MANAGEMENT
# =============================================

@login_required(login_url='/login/')
def appointments(request):
    """Appointments page - for patients only"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard')
    
    try:
        patient = Patient.objects.get(user=request.user)
        today = datetime.now()
        
        # Get all appointments for this patient
        all_appointments = Appointment.objects.filter(patient=patient).select_related(
            'assigned_doctor', 'assigned_doctor__user', 'vaccine'
        ).order_by('-scheduled_date')
        
        # Statistics
        upcoming_count = all_appointments.filter(
            scheduled_date__gte=today, 
            status__in=['scheduled', 'confirmed']
        ).count()
        completed_count = all_appointments.filter(status='completed').count()
        pending_count = all_appointments.filter(status='scheduled').count()
        cancelled_count = all_appointments.filter(status='cancelled').count()
        
        # Upcoming appointments (next 30 days)
        upcoming_appointments = all_appointments.filter(
            scheduled_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).order_by('scheduled_date')[:10]
        
        # Appointment history (last 6 months)
        six_months_ago = today - timedelta(days=180)
        appointment_history = all_appointments.filter(
            scheduled_date__gte=six_months_ago
        ).exclude(status__in=['scheduled', 'confirmed']).order_by('-scheduled_date')[:20]
        
        # Available doctors for booking
        available_doctors = Doctor.objects.filter(is_available=True).select_related('user', 'department')
        
        # Available departments
        departments = Department.objects.filter(is_active=True)
        
        # Available vaccines
        vaccines = Vaccine.objects.filter(is_active=True)
        
        context = {
            'appointments': all_appointments,
            'upcoming_appointments': upcoming_appointments,
            'appointment_history': appointment_history,
            'upcoming_count': upcoming_count,
            'completed_count': completed_count,
            'pending_count': pending_count,
            'cancelled_count': cancelled_count,
            'total_appointments': all_appointments.count(),
            'patient': patient,
            'available_doctors': available_doctors,
            'departments': departments,
            'vaccines': vaccines,
            'current_date': today.strftime("%B %d, %Y"),
        }
        
    except Patient.DoesNotExist:
        messages.warning(request, 'Please complete your patient profile to view appointments.')
        context = {
            'appointments': [],
            'upcoming_appointments': [],
            'appointment_history': [],
            'upcoming_count': 0,
            'completed_count': 0,
            'pending_count': 0,
            'cancelled_count': 0,
            'total_appointments': 0,
            'available_doctors': [],
            'departments': [],
            'current_date': datetime.now().strftime("%B %d, %Y"),
        }
    
    return render(request, 'appointments.html', context)


@login_required(login_url='/login/')
def create_appointment(request):
    """Create new appointment"""
    if request.method == 'POST':
        try:
            patient = Patient.objects.get(user=request.user)
            
            appointment = Appointment(
                patient=patient,
                appointment_type=request.POST.get('appointment_type'),
                scheduled_date=datetime.strptime(
                    f"{request.POST.get('appointment_date')} {request.POST.get('appointment_time')}", 
                    "%Y-%m-%d %H:%M"
                ),
                duration=request.POST.get('duration', 30),
                reason=request.POST.get('reason'),
                symptoms=request.POST.get('symptoms', ''),
                status='scheduled'
            )
            
            if request.POST.get('assigned_doctor'):
                appointment.assigned_doctor_id = request.POST.get('assigned_doctor')
            
            if request.POST.get('vaccine'):
                appointment.vaccine_id = request.POST.get('vaccine')
                appointment.is_vaccination = True
                appointment.appointment_type = 'vaccination'
            
            appointment.save()
            messages.success(request, 'Appointment created successfully!')
            
        except Patient.DoesNotExist:
            messages.error(request, 'Patient profile not found.')
        except Exception as e:
            messages.error(request, f'Error creating appointment: {str(e)}')
        
        return redirect('appointments')
    
    return redirect('appointments')


@login_required(login_url='/login/')
def update_appointment_status(request, appointment_id):
    """Update appointment status"""
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permission
        if appointment.patient.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to update this appointment.')
            return redirect('appointments')
        
        new_status = request.POST.get('status')
        if new_status in dict(Appointment.APPOINTMENT_STATUS):
            appointment.status = new_status
            appointment.save()
            messages.success(request, f'Appointment status updated to {appointment.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('appointments')


@login_required(login_url='/login/')
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permission
        if appointment.patient.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to cancel this appointment.')
            return redirect('appointments')
        
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    
    return redirect('appointments')


# =============================================
# CONSULTATIONS MANAGEMENT
# =============================================

@login_required(login_url='/login/')
def consultation(request):
    """Consultation page - for patients only"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard')
    
    try:
        patient = Patient.objects.get(user=request.user)
        
        # Get patient's consultations
        consultations = Consultation.objects.filter(patient=patient).select_related(
            'doctor', 'doctor__user'
        ).order_by('-consultation_date')
        
        # Get available doctors for new consultation
        available_doctors = Doctor.objects.filter(is_available=True).select_related('user', 'department')[:5]
        
        context = {
            'patient': patient,
            'consultations': consultations,
            'available_doctors': available_doctors,
            'total_consultations': consultations.count(),
        }
    except Patient.DoesNotExist:
        context = {
            'consultations': [],
            'available_doctors': [],
            'total_consultations': 0,
        }
    
    return render(request, 'consultation.html', context)


@login_required(login_url='/login/')
def create_consultation(request):
    """Create new consultation request"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            patient = Patient.objects.get(user=request.user)
            
            # Create consultation
            consultation = Consultation(
                patient=patient,
                doctor_id=request.POST.get('doctor'),
                symptoms=request.POST.get('symptoms'),
                description=request.POST.get('description', ''),
                status='pending'
            )
            consultation.save()
            
            messages.success(request, 'Consultation request sent successfully! A doctor will respond shortly.')
            
        except Patient.DoesNotExist:
            messages.error(request, 'Patient profile not found.')
        except Exception as e:
            messages.error(request, f'Error creating consultation: {str(e)}')
        
        return redirect('consultation')
    
    return redirect('consultation')


@login_required(login_url='/login/')
def consultation_management(request):
    """Consultation management (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('consultation')
    
    consultations = Consultation.objects.select_related(
        'patient', 'patient__user', 'doctor', 'doctor__user'
    ).all()
    
    context = {
        'consultations': consultations,
        'pending_count': consultations.filter(status='pending').count(),
        'in_progress_count': consultations.filter(status='in_progress').count(),
        'completed_count': consultations.filter(status='completed').count(),
    }
    return render(request, 'consultation_management.html', context)


# =============================================
# PRESCRIPTIONS MANAGEMENT
# =============================================

@login_required(login_url='/login/')
def prescriptions(request):
    """Prescriptions page - for patients only"""
    if request.user.is_staff or request.user.is_superuser:
        messages.warning(request, 'This page is for patients only.')
        return redirect('dashboard')
    
    try:
        patient = Patient.objects.get(user=request.user)
        prescriptions_list = Prescription.objects.filter(patient=patient).select_related(
            'doctor', 'doctor__user'
        ).prefetch_related('medications').order_by('-date_issued')
        
        # Statistics
        active_prescriptions = prescriptions_list.filter(status='active').count()
        total_prescriptions = prescriptions_list.count()
        
        # Get latest prescription date
        latest_prescription = prescriptions_list.first()
        last_prescription_date = "2 weeks ago"
        if latest_prescription:
            days_ago = (datetime.now().date() - latest_prescription.date_issued).days
            if days_ago == 0:
                last_prescription_date = "Today"
            elif days_ago == 1:
                last_prescription_date = "Yesterday"
            else:
                last_prescription_date = f"{days_ago} days ago"
        
        context = {
            'prescriptions': prescriptions_list,
            'active_prescriptions': active_prescriptions,
            'total_prescriptions': total_prescriptions,
            'last_prescription_date': last_prescription_date,
        }
    except Patient.DoesNotExist:
        context = {
            'prescriptions': [],
            'active_prescriptions': 0,
            'total_prescriptions': 0,
            'last_prescription_date': 'N/A',
        }
    
    return render(request, 'prescriptions.html', context)


@login_required(login_url='/login/')
def prescription_detail(request, prescription_id):
    """View prescription details"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    # Check permission
    if prescription.patient.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this prescription.')
        return redirect('prescriptions')
    
    context = {
        'prescription': prescription,
    }
    return render(request, 'prescription_detail.html', context)


@login_required(login_url='/login/')
def request_refill(request, prescription_id):
    """Request prescription refill"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    if prescription.patient.user != request.user:
        messages.error(request, 'You do not have permission to request refill for this prescription.')
        return redirect('prescriptions')
    
    if request.method == 'POST':
        # Create refill request logic here
        messages.success(request, f'Refill request for prescription #{prescription.id} has been sent to your pharmacy.')
    
    return redirect('prescriptions')


@login_required(login_url='/login/')
def create_prescription(request):
    """Create new prescription (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('prescriptions')
    
    if request.method == 'POST':
        prescription_form = PrescriptionForm(request.POST)
        if prescription_form.is_valid():
            prescription = prescription_form.save()
            
            # Handle medications
            medication_names = request.POST.getlist('medication_name')
            medication_dosages = request.POST.getlist('medication_dosage')
            medication_frequencies = request.POST.getlist('medication_frequency')
            medication_durations = request.POST.getlist('medication_duration')
            medication_instructions = request.POST.getlist('medication_instructions')
            medication_purposes = request.POST.getlist('medication_purpose')
            
            for i in range(len(medication_names)):
                if medication_names[i]:
                    Medication.objects.create(
                        prescription=prescription,
                        name=medication_names[i],
                        dosage=medication_dosages[i],
                        frequency=medication_frequencies[i],
                        duration=medication_durations[i],
                        instructions=medication_instructions[i],
                        purpose=medication_purposes[i]
                    )
            
            messages.success(request, 'Prescription created successfully!')
            return redirect('prescription_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        prescription_form = PrescriptionForm()
    
    return render(request, 'create_prescription.html', {'prescription_form': prescription_form})


@login_required(login_url='/login/')
def prescription_management(request):
    """Prescription management (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('prescriptions')
    
    prescriptions_list = Prescription.objects.select_related(
        'patient', 'patient__user', 'doctor', 'doctor__user'
    ).prefetch_related('medications').all()
    
    context = {
        'prescriptions': prescriptions_list,
        'active_count': prescriptions_list.filter(status='active').count(),
        'completed_count': prescriptions_list.filter(status='completed').count(),
    }
    return render(request, 'prescription_management.html', context)


# =============================================
# MEDICAL RECORDS MANAGEMENT
# =============================================

@login_required(login_url='/login/')
def medical_records(request):
    """Medical records page - for patients only"""
    if request.user.is_staff or request.user.is_superuser:
        messages.warning(request, 'This page is for patients only.')
        return redirect('dashboard')
    
    try:
        patient = Patient.objects.get(user=request.user)
        medical_record = MedicalRecord.objects.filter(patient=patient).first()
        
        # Get all medical data
        appointments = Appointment.objects.filter(patient=patient).order_by('-scheduled_date')[:10]
        prescriptions = Prescription.objects.filter(patient=patient).order_by('-date_issued')[:10]
        consultations = Consultation.objects.filter(patient=patient).order_by('-consultation_date')[:10]
        vaccinations = VaccinationRecord.objects.filter(patient=patient).select_related('vaccine').order_by('-date_administered')
        
        if medical_record:
            # Convert JSON fields to Python objects for template
            medical_data = {
                'personal_info': {
                    'full_name': medical_record.full_name,
                    'date_of_birth': medical_record.date_of_birth.strftime("%B %d, %Y"),
                    'age': medical_record.age,
                    'gender': medical_record.gender,
                    'blood_type': medical_record.blood_type,
                    'allergies': medical_record.allergies,
                    'emergency_contact': medical_record.emergency_contact,
                    'address': medical_record.address,
                    'phone': medical_record.phone,
                    'email': medical_record.email,
                    'insurance_number': medical_record.insurance_number,
                    'primary_physician': medical_record.primary_physician,
                },
                'growth_history': medical_record.growth_history,
                'vaccination_records': medical_record.vaccination_records,
                'medical_history': medical_record.medical_history,
                'last_medical_details': medical_record.last_medical_details,
                'family_history': medical_record.family_history,
                'developmental_milestones': medical_record.developmental_milestones,
            }
        else:
            # Create data from related records if no medical record exists
            medical_data = {
                'personal_info': {
                    'full_name': f"{patient.first_name} {patient.last_name}",
                    'date_of_birth': patient.date_of_birth.strftime("%B %d, %Y"),
                    'age': str(patient.age()),
                    'gender': patient.get_gender_display(),
                    'blood_type': patient.blood_type or 'Unknown',
                    'allergies': patient.allergies or 'None recorded',
                    'emergency_contact': 'Not specified',
                    'address': 'Not specified',
                    'phone': patient.patient_phone or 'Not specified',
                    'email': patient.patient_email or 'Not specified',
                    'insurance_number': 'Not specified',
                    'primary_physician': 'Not specified',
                },
                'growth_history': [],
                'vaccination_records': [],
                'medical_history': [],
                'last_medical_details': {},
                'family_history': {},
                'developmental_milestones': [],
            }
            
            # Add vaccination records
            for vacc in vaccinations:
                medical_data['vaccination_records'].append({
                    'vaccine': vacc.vaccine.name,
                    'date': vacc.date_administered.strftime("%b %d, %Y") if vacc.date_administered else 'Scheduled',
                    'dose': f"Dose {vacc.dose_number}",
                    'location': vacc.administering_facility or 'Not specified',
                    'batch': vacc.lot_number or 'N/A',
                })
        
        context = {
            'medical_data': medical_data,
            'appointments': appointments,
            'prescriptions': prescriptions,
            'consultations': consultations,
            'vaccinations': vaccinations,
            'current_date': datetime.now().strftime("%B %d, %Y"),
            'has_medical_record': medical_record is not None,
        }
        
    except Patient.DoesNotExist:
        context = {
            'medical_data': {},
            'appointments': [],
            'prescriptions': [],
            'consultations': [],
            'vaccinations': [],
            'current_date': datetime.now().strftime("%B %d, %Y"),
            'has_medical_record': False,
        }
    
    return render(request, 'medical_records.html', context)


@login_required(login_url='/login/')
def create_medical_record(request):
    """Create new medical record (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('medical_records')
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            medical_record = form.save(commit=False)
            
            # Handle JSON fields
            growth_history = request.POST.get('growth_history', '[]')
            vaccination_records = request.POST.get('vaccination_records', '[]')
            medical_history = request.POST.get('medical_history', '[]')
            last_medical_details = request.POST.get('last_medical_details', '{}')
            family_history = request.POST.get('family_history', '{}')
            developmental_milestones = request.POST.get('developmental_milestones', '[]')
            
            try:
                medical_record.growth_history = json.loads(growth_history)
                medical_record.vaccination_records = json.loads(vaccination_records)
                medical_record.medical_history = json.loads(medical_history)
                medical_record.last_medical_details = json.loads(last_medical_details)
                medical_record.family_history = json.loads(family_history)
                medical_record.developmental_milestones = json.loads(developmental_milestones)
            except json.JSONDecodeError:
                messages.error(request, 'Invalid JSON data in one of the fields.')
                return render(request, 'create_medical_record.html', {'form': form})
            
            medical_record.save()
            messages.success(request, 'Medical record created successfully!')
            return redirect('medical_record_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MedicalRecordForm()
    
    return render(request, 'create_medical_record.html', {'form': form})


@login_required(login_url='/login/')
def medical_record_management(request):
    """Medical record management (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('medical_records')
    
    medical_records_list = MedicalRecord.objects.select_related('patient', 'patient__user').all()
    
    context = {
        'medical_records': medical_records_list,
        'total_records': medical_records_list.count(),
    }
    return render(request, 'medical_record_management.html', context)


@login_required(login_url='/login/')
def download_medical_record(request):
    """Generate and download medical record as HTML/PDF"""
    try:
        patient = Patient.objects.get(user=request.user)
        medical_record = MedicalRecord.objects.filter(patient=patient).first()
        
        if medical_record:
            medical_data = {
                'personal_info': {
                    'full_name': medical_record.full_name,
                    'date_of_birth': medical_record.date_of_birth.strftime("%B %d, %Y"),
                    'age': medical_record.age,
                    'gender': medical_record.gender,
                    'blood_type': medical_record.blood_type,
                    'allergies': medical_record.allergies,
                    'emergency_contact': medical_record.emergency_contact,
                    'address': medical_record.address,
                    'primary_physician': medical_record.primary_physician,
                    'insurance_number': medical_record.insurance_number
                },
                'growth_history': medical_record.growth_history,
                'vaccination_records': medical_record.vaccination_records,
                'last_medical_details': medical_record.last_medical_details,
                'medical_history': medical_record.medical_history
            }
        else:
            # Get data from related records
            vaccinations = VaccinationRecord.objects.filter(patient=patient).select_related('vaccine')
            vaccination_records = []
            for vacc in vaccinations:
                vaccination_records.append({
                    'vaccine': vacc.vaccine.name,
                    'date': vacc.date_administered.strftime("%b %d, %Y") if vacc.date_administered else 'Scheduled',
                    'dose': f"Dose {vacc.dose_number}",
                })
            
            medical_data = {
                'personal_info': {
                    'full_name': f"{patient.first_name} {patient.last_name}",
                    'date_of_birth': patient.date_of_birth.strftime("%B %d, %Y"),
                    'age': str(patient.age()),
                    'gender': patient.get_gender_display(),
                    'blood_type': patient.blood_type or 'Unknown',
                    'allergies': patient.allergies or 'None recorded',
                    'emergency_contact': 'Not specified',
                    'address': 'Not specified',
                    'primary_physician': 'Not specified',
                    'insurance_number': 'Not specified'
                },
                'growth_history': [],
                'vaccination_records': vaccination_records,
                'last_medical_details': {},
                'medical_history': []
            }
        
        context = {
            'medical_data': medical_data,
            'current_date': datetime.now().strftime("%B %d, %Y"),
            'download_date': datetime.now().strftime("%B %d, %Y %H:%M")
        }
        
        html_string = render_to_string('medical_record_pdf.html', context)
        
        response = HttpResponse(html_string, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="medical_record_{datetime.now().strftime("%Y%m%d_%H%M")}.html"'
        
        return response
        
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('medical_records')
    except Exception as e:
        print(f"Error generating medical record: {str(e)}")
        messages.error(request, 'Error generating medical record. Please try again.')
        return redirect('medical_records')


# =============================================
# VACCINATION HISTORY MANAGEMENT
# =============================================

@login_required(login_url='/login/')
def vaccination_history(request):
    """Vaccination history - for patients only"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard')
    
    try:
        patient = Patient.objects.get(user=request.user)
        vaccination_records = VaccinationRecord.objects.filter(patient=patient).select_related('vaccine').order_by('-date_administered')
        
        # Statistics
        completed_count = vaccination_records.filter(status='administered').count()
        upcoming_count = vaccination_records.filter(status='scheduled').count()
        
        # Find due this month
        today = datetime.now().date()
        next_month = today + timedelta(days=30)
        due_this_month = vaccination_records.filter(
            next_due_date__gte=today,
            next_due_date__lte=next_month,
            status='scheduled'
        ).count()
        
        # Find overdue
        overdue_count = vaccination_records.filter(
            next_due_date__lt=today,
            status='scheduled'
        ).count()
        
        # Prepare data for template
        vaccination_data = []
        completed_list = []
        upcoming_list = []
        
        for record in vaccination_records:
            status = 'completed' if record.status == 'administered' else 'in_progress' if record.status == 'scheduled' else 'due_soon'
            actions = 'view_certificate' if record.status == 'administered' else 'schedule'
            
            vaccine_info = {
                'name': record.vaccine.name,
                'type': f'Dose {record.dose_number} of {record.total_doses}',
                'status': status,
                'date_given': record.date_administered.strftime("%b %d, %Y") if record.date_administered else '-',
                'next_dose': record.next_due_date.strftime("%b %d, %Y") if record.next_due_date else '-',
                'location': record.administering_facility or 'Not specified',
                'batch_no': record.lot_number or '-',
                'actions': actions
            }
            
            vaccination_data.append(vaccine_info)
            
            if record.status == 'administered':
                completed_list.append(vaccine_info)
            else:
                upcoming_list.append(vaccine_info)
        
        context = {
            'vaccination_data': vaccination_data,
            'completed_list': completed_list[:5],
            'upcoming_list': upcoming_list[:5],
            'completed_count': completed_count,
            'upcoming_count': upcoming_count,
            'due_this_month': due_this_month,
            'overdue_count': overdue_count,
            'total_count': vaccination_records.count(),
            'vaccines': Vaccine.objects.filter(is_active=True),
        }
    except Patient.DoesNotExist:
        context = {
            'vaccination_data': [],
            'completed_list': [],
            'upcoming_list': [],
            'completed_count': 0,
            'upcoming_count': 0,
            'due_this_month': 0,
            'overdue_count': 0,
            'total_count': 0,
        }
    
    return render(request, 'vaccination_history.html', context)


@login_required(login_url='/login/')
def schedule_vaccination(request):
    """Schedule a new vaccination"""
    if request.method == 'POST':
        try:
            patient = Patient.objects.get(user=request.user)
            vaccine_id = request.POST.get('vaccine_id')
            scheduled_date = request.POST.get('scheduled_date')
            
            if vaccine_id and scheduled_date:
                vaccine = Vaccine.objects.get(id=vaccine_id)
                
                # Get next dose number
                existing_records = VaccinationRecord.objects.filter(
                    patient=patient,
                    vaccine=vaccine
                ).count()
                
                next_dose = existing_records + 1
                
                # Calculate next due date (simplified - in real app, use vaccine schedule)
                next_due_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date() + timedelta(days=vaccine.days_between_doses or 30)
                
                vaccination_record = VaccinationRecord(
                    patient=patient,
                    vaccine=vaccine,
                    dose_number=next_dose,
                    total_doses=vaccine.doses_required,
                    date_administered=None,
                    next_due_date=next_due_date,
                    status='scheduled'
                )
                vaccination_record.save()
                
                messages.success(request, f'{vaccine.name} scheduled successfully!')
            else:
                messages.error(request, 'Please select a vaccine and date.')
                
        except Patient.DoesNotExist:
            messages.error(request, 'Patient profile not found.')
        except Vaccine.DoesNotExist:
            messages.error(request, 'Vaccine not found.')
        except Exception as e:
            messages.error(request, f'Error scheduling vaccination: {str(e)}')
        
        return redirect('vaccination_history')
    
    return redirect('vaccination_history')


@login_required(login_url='/login/')
def download_vaccination_certificate(request, record_id):
    """Download vaccination certificate"""
    try:
        record = get_object_or_404(VaccinationRecord, id=record_id)
        
        if record.patient.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to download this certificate.')
            return redirect('vaccination_history')
        
        # Create certificate HTML
        context = {
            'record': record,
            'patient': record.patient,
            'vaccine': record.vaccine,
            'current_date': datetime.now().strftime("%B %d, %Y"),
        }
        
        html_string = render_to_string('vaccination_certificate.html', context)
        
        response = HttpResponse(html_string, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="vaccination_certificate_{record.id}.html"'
        
        return response
        
    except Exception as e:
        messages.error(request, 'Error generating certificate.')
        return redirect('vaccination_history')


@login_required(login_url='/login/')
def create_vaccination_record(request):
    """Create new vaccination record (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('vaccination_history')

    if request.method == 'POST':
        form = VaccinationRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vaccination record created successfully!')
            return redirect('vaccination_record_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VaccinationRecordForm()

    return render(request, 'create_vaccination_record.html', {'form': form})

@login_required(login_url='/login/')
def vaccination_record_management(request):
    """Vaccination record management (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('vaccination_history')
    
    vaccination_records = VaccinationRecord.objects.select_related(
        'patient', 'patient__user', 'vaccine'
    ).all()
    
    context = {
        'vaccination_records': vaccination_records,
        'total_records': vaccination_records.count(),
        'administered_count': vaccination_records.filter(status='administered').count(),
        'scheduled_count': vaccination_records.filter(status='scheduled').count(),
    }
    return render(request, 'vaccination_record_management.html', context)


# =============================================
# API ENDPOINTS
# =============================================

@login_required(login_url='/login/')
def get_departments(request):
    """API endpoint to get all departments"""
    departments = Department.objects.filter(is_active=True)
    departments_data = [
        {
            'id': dept.id,
            'name': dept.name,
            'description': dept.description
        }
        for dept in departments
    ]
    return JsonResponse({'departments': departments_data})


@login_required(login_url='/login/')
def get_available_doctors(request):
    """API endpoint to get available doctors by department"""
    department_id = request.GET.get('department_id')
    if department_id:
        doctors = Doctor.objects.filter(
            department_id=department_id, 
            is_available=True
        ).select_related('user')
        doctors_data = [
            {
                'id': doctor.id,
                'name': f"Dr. {doctor.user.get_full_name()}",
                'specialization': doctor.specialization,
                'consultation_fee': float(doctor.consultation_fee),
                'department': doctor.department.name,
            }
            for doctor in doctors
        ]
        return JsonResponse({'doctors': doctors_data})
    return JsonResponse({'doctors': []})


@login_required(login_url='/login/')
def get_available_slots(request):
    """API endpoint to get available time slots for a doctor"""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    
    if doctor_id and date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Get existing appointments for that doctor on that date
            existing_appointments = Appointment.objects.filter(
                assigned_doctor_id=doctor_id,
                scheduled_date__date=selected_date,
                status__in=['scheduled', 'confirmed']
            ).values_list('scheduled_date__time', flat=True)
            
            # Generate available slots (every 30 minutes from 9 AM to 5 PM)
            available_slots = []
            start_time = datetime.strptime('09:00', '%H:%M').time()
            end_time = datetime.strptime('17:00', '%H:%M').time()
            
            current_time = datetime.combine(selected_date, start_time)
            end_datetime = datetime.combine(selected_date, end_time)
            
            while current_time < end_datetime:
                time_slot = current_time.time()
                if time_slot not in existing_appointments:
                    available_slots.append(current_time.strftime('%H:%M'))
                current_time += timedelta(minutes=30)
            
            return JsonResponse({'slots': available_slots})
            
        except ValueError:
            return JsonResponse({'slots': []})
    
    return JsonResponse({'slots': []})


@login_required(login_url='/login/')
def get_vaccines(request):
    """API endpoint to get all vaccines"""
    vaccines = Vaccine.objects.filter(is_active=True)
    vaccines_data = [
        {
            'id': vaccine.id,
            'name': vaccine.name,
            'short_name': vaccine.short_name,
            'vaccine_type': vaccine.vaccine_type,
            'doses_required': vaccine.doses_required,
            'days_between_doses': vaccine.days_between_doses,
        }
        for vaccine in vaccines
    ]
    return JsonResponse({'vaccines': vaccines_data})

@login_required
def add_patient(request):
    """Add a new patient"""
    if request.method == 'POST':
        try:
            # Create the patient
            patient = Patient.objects.create(
                user=request.user,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                date_of_birth=request.POST.get('date_of_birth'),
                gender=request.POST.get('gender', 'U'),
                blood_type=request.POST.get('blood_type'),
                patient_phone=request.POST.get('patient_phone'),
                patient_email=request.POST.get('patient_email'),
            )
            messages.success(request, f'Patient {patient.full_name} added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding patient: {str(e)}')
        
        return redirect('dashboard')
    
    # If not POST, redirect to dashboard
    return redirect('dashboard')

@login_required
def patient_detail(request, patient_id):
    """View patient details"""
    try:
        # Get the patient
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Check permission - user can only view their own patients unless they're staff
        if patient.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to view this patient.')
            return redirect('dashboard')
        
        # Get patient's vaccination records
        vaccination_records = VaccinationRecord.objects.filter(patient=patient).select_related('vaccine').order_by('-date_administered')
        
        # Get patient's appointments
        appointments = Appointment.objects.filter(patient=patient).order_by('-scheduled_date')
        
        # Calculate statistics
        total_vaccinations = vaccination_records.count()
        completed_vaccinations = vaccination_records.filter(status='administered').count()
        upcoming_vaccinations = vaccination_records.filter(status='scheduled').count()
        
        context = {
            'patient': patient,
            'vaccination_records': vaccination_records,
            'appointments': appointments,
            'total_vaccinations': total_vaccinations,
            'completed_vaccinations': completed_vaccinations,
            'upcoming_vaccinations': upcoming_vaccinations,
        }
        
        return render(request, 'patient_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error viewing patient: {str(e)}')
        return redirect('dashboard')
@login_required
def edit_patient(request, patient_id):
    """Edit patient information"""
    try:
        # Get the patient
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Check permission - user can only edit their own patients unless they're staff
        if patient.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to edit this patient.')
            return redirect('dashboard')
        
        if request.method == 'POST':
            # Update patient fields from form data
            patient.first_name = request.POST.get('first_name', patient.first_name)
            patient.last_name = request.POST.get('last_name', patient.last_name)
            patient.date_of_birth = request.POST.get('date_of_birth', patient.date_of_birth)
            patient.gender = request.POST.get('gender', patient.gender)
            patient.blood_type = request.POST.get('blood_type', patient.blood_type)
            patient.patient_phone = request.POST.get('patient_phone', patient.patient_phone)
            patient.patient_email = request.POST.get('patient_email', patient.patient_email)
            patient.allergies = request.POST.get('allergies', patient.allergies)
            patient.medical_conditions = request.POST.get('medical_conditions', patient.medical_conditions)
            patient.current_medications = request.POST.get('current_medications', patient.current_medications)
            patient.save()
            
            messages.success(request, f'Patient {patient.full_name} updated successfully!')
            return redirect('patient_detail', patient_id=patient.id)
        
        # GET request - display edit form
        context = {
            'patient': patient,
        }
        return render(request, 'edit_patient.html', context)
        
    except Exception as e:
        messages.error(request, f'Error editing patient: {str(e)}')
        return redirect('dashboard')
    
@login_required
def delete_patient(request, patient_id):
    """Delete a patient"""
    if request.method == 'POST':
        try:
            # Get the patient
            patient = get_object_or_404(Patient, id=patient_id)
            
            # Check permission
            if patient.user != request.user and not request.user.is_staff:
                messages.error(request, 'You do not have permission to delete this patient.')
                return redirect('dashboard')
            
            # Store name for success message
            patient_name = patient.full_name
            
            # Delete the patient
            patient.delete()
            
            messages.success(request, f'Patient {patient_name} deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting patient: {str(e)}')
    
    return redirect('dashboard')


@login_required
def vaccination_schedule_management(request):
    """Vaccination schedule management page for admins"""
    # Check if user is admin/staff
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Handle form submission
    if request.method == 'POST':
        form = VaccinationScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            
            # ============ CREATE NOTIFICATION USING GET_OR_CREATE (NO DUPLICATES) ============
            if schedule.is_published:
                # This will either get the existing notification or create a new one
                notification, created = Notification.objects.get_or_create(
                    schedule=schedule,  # Unique constraint
                    defaults={
                        'title': f"New Vaccination Schedule: {schedule.title}",
                        'message': f"A new vaccination schedule has been created for {schedule.scheduled_date} at {schedule.location}. {schedule.description}",
                        'notification_type': 'info',
                        'created_by': request.user,
                        'is_sent': True,
                        'sent_at': timezone.now(),
                        'is_for_all': True
                    }
                )
                
                if created:
                    messages.success(request, 'Vaccination schedule created successfully! New notification sent to all patients.')
                else:
                    # Update existing notification
                    notification.title = f"New Vaccination Schedule: {schedule.title}"
                    notification.message = f"A new vaccination schedule has been created for {schedule.scheduled_date} at {schedule.location}. {schedule.description}"
                    notification.sent_at = timezone.now()
                    notification.save()
                    messages.success(request, 'Vaccination schedule created successfully! Existing notification updated.')
            else:
                messages.success(request, 'Vaccination schedule created successfully (draft mode).')
            
            return redirect('vaccination_schedule_management')
            
        else:
            messages.error(request, 'Please correct the errors below.')
    
    # For GET requests or failed POST
    form = VaccinationScheduleForm()
    
    # Get all schedules
    from datetime import date
    schedules = VaccinationSchedule.objects.all().order_by('-scheduled_date')
    
    # Get vaccines for the form
    vaccines = Vaccine.objects.filter(is_active=True)
    
    # ============ ADD NOTIFICATIONS TO CONTEXT (ONLY FOR DISPLAY, NOT COUNTS) ============
    try:
        notifications = Notification.objects.all().order_by('-created_at')[:10]
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        notifications = []
    
    context = {
        'schedule_notifications': Notification.objects.filter(schedule__isnull=False).order_by('-created_at'),
        'form': form,
        'upcoming_count': schedules.filter(scheduled_date__gte=date.today(), is_active=True).count(),
        'total_count': schedules.count(),
        'vaccines': vaccines,
        'notifications': notifications,
    }
    return render(request, 'vaccination_schedule_content.html', context)


@login_required
def delete_vaccination_schedule(request, schedule_id):
    """Delete a vaccination schedule"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        schedule = get_object_or_404(VaccinationSchedule, id=schedule_id)
        schedule.delete()
        messages.success(request, 'Vaccination schedule deleted successfully!')
    
    return redirect('vaccination_schedule_management')


@login_required
def patient_vaccination_schedules(request):
    """View for patients to see available vaccination schedules"""
    today = date.today()
    schedules = VaccinationSchedule.objects.filter(
        scheduled_date__gte=today,
        is_active=True,
        is_published=True
    ).order_by('scheduled_date', 'start_time')
    
    context = {
        'schedules': schedules,
    }
    return render(request, 'patient_schedules.html', context)


@login_required
def register_for_schedule(request, schedule_id):
    """Allow patients to register for a vaccination schedule"""
    schedule = get_object_or_404(VaccinationSchedule, id=schedule_id, is_active=True, is_published=True)
    
    if request.method == 'POST':
        # Check if schedule is full
        if schedule.is_full():
            messages.error(request, 'This vaccination event is already full.')
            return redirect('patient_schedules')
        
        # Here you would create a registration record
        # You might want to create a Registration model to track this
        
        schedule.registered_count += 1
        schedule.save()
        
        messages.success(request, f'You have successfully registered for {schedule.title} on {schedule.scheduled_date}.')
    
    return redirect('patient_schedules')

@login_required
def my_notifications(request):
    """View for patients to see their notifications"""
    user = request.user
    filter_type = request.GET.get('filter', 'all')
    
    # Base queryset
    base_notifications = Notification.objects.filter(
        Q(recipient=user) | Q(is_for_all=True)
    ).distinct()
    
    print(f"Total notifications for user: {base_notifications.count()}")
    print(f"Unread count: {base_notifications.filter(is_read=False).count()}")
    
    # Apply filter
    if filter_type == 'unread':
        notifications = base_notifications.filter(is_read=False)
    else:
        notifications = base_notifications
    
    notifications = notifications.order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'filter_type': filter_type,
        'total_count': base_notifications.count(),
        'unread_count': base_notifications.filter(is_read=False).count(),
    }
    return render(request, 'notifications.html', context)

@login_required
def edit_vaccination_schedule(request, schedule_id):
    """Edit a vaccination schedule"""
    print(f"\n{'='*50}")
    print(f"EDIT SCHEDULE VIEW CALLED")
    print(f"Schedule ID: {schedule_id}")
    print(f"Method: {request.method}")
    print(f"{'='*50}\n")
    
    # Check if user is admin/staff
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get the schedule
    schedule = get_object_or_404(VaccinationSchedule, id=schedule_id)
    
    if request.method == 'POST':
        print("POST data received:")
        for key, value in request.POST.items():
            print(f"  {key}: {value}")
        
        # Update schedule fields
        schedule.title = request.POST.get('title', schedule.title)
        schedule.description = request.POST.get('description', schedule.description)
        
        vaccine_id = request.POST.get('vaccine')
        if vaccine_id:
            schedule.vaccine_id = vaccine_id
        else:
            schedule.vaccine = None
            
        schedule.scheduled_date = request.POST.get('scheduled_date', schedule.scheduled_date)
        schedule.start_time = request.POST.get('start_time', schedule.start_time)
        schedule.end_time = request.POST.get('end_time', schedule.end_time)
        schedule.location = request.POST.get('location', schedule.location)
        schedule.address = request.POST.get('address', schedule.address)
        schedule.target_age_groups = request.POST.get('target_age_groups', schedule.target_age_groups)
        schedule.max_capacity = request.POST.get('max_capacity', schedule.max_capacity)
        schedule.contact_phone = request.POST.get('contact_phone', schedule.contact_phone)
        schedule.contact_email = request.POST.get('contact_email', schedule.contact_email)
        schedule.notes = request.POST.get('notes', schedule.notes)
        
        # Handle checkboxes
        schedule.is_for_all = request.POST.get('is_for_all') == 'on'
        schedule.requires_registration = request.POST.get('requires_registration') == 'on'
        schedule.is_published = request.POST.get('is_published') == 'on'
        schedule.is_active = request.POST.get('is_active') == 'on' if request.POST.get('is_active') else True
        
        schedule.save()
        print(f"Schedule saved: {schedule.title}")
        
        messages.success(request, f'Schedule "{schedule.title}" updated successfully!')
        return redirect('/dashboard/#schedule_management')
    
    # GET request - show edit form
    vaccines = Vaccine.objects.filter(is_active=True)
    context = {
        'schedule': schedule,
        'vaccines': vaccines,
    }
    return render(request, 'edit_vaccination_schedule.html', context)

@login_required
def create_vaccination_schedule(request):
    """Create a new vaccination schedule (separate page)"""
    # Check if user is admin/staff
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = VaccinationScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            
            # ============ CREATE SINGLE NOTIFICATION (NO DUPLICATES) ============
            try:
                if schedule.is_published:
                    # Delete any existing notifications for this schedule (cleanup)
                    deleted_count = Notification.objects.filter(schedule=schedule).delete()[0]
                    if deleted_count > 0:
                        print(f"Deleted {deleted_count} existing notification(s) for schedule {schedule.id}")
                    
                    # Create ONE notification for all patients
                    Notification.objects.create(
                        title=f"New Vaccination Schedule: {schedule.title}",
                        message=f"A new vaccination schedule has been created for {schedule.scheduled_date} at {schedule.location}. {schedule.description}",
                        notification_type='info',
                        schedule=schedule,
                        created_by=request.user,
                        is_sent=True,
                        sent_at=timezone.now(),
                        is_for_all=True  # This marks it as visible to ALL patients
                    )
                    
                    messages.success(request, 'Vaccination schedule created successfully! Notification sent to all patients.')
                else:
                    messages.success(request, 'Vaccination schedule created successfully (draft mode).')
                    
            except Exception as e:
                print(f"Error creating notification: {e}")
                messages.warning(request, 'Schedule created but there was an issue sending notification.')
            
            return redirect('/dashboard/#schedule_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VaccinationScheduleForm()
    
    context = {
        'form': form,
        'vaccines': Vaccine.objects.filter(is_active=True),
    }
    return render(request, 'create_vaccination_schedule.html', context)

@csrf_exempt
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id)
            if notification.recipient == request.user or notification.is_for_all:
                notification.is_read = True
                notification.save()
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(
            Q(recipient=request.user) | Q(is_for_all=True),
            is_read=False
        ).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_notification(request, notification_id):
    if request.method == 'DELETE':
        try:
            notification = Notification.objects.get(id=notification_id)
            if notification.recipient == request.user or notification.is_for_all:
                notification.delete()
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_all_notifications(request):
    if request.method == 'DELETE':
        Notification.objects.filter(
            Q(recipient=request.user) | Q(is_for_all=True)
        ).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def notification_detail_api(request, notification_id):
    """API endpoint to get notification details"""
    try:
        notification = Notification.objects.get(id=notification_id)
        return JsonResponse({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.get_notification_type_display(),
            'created': notification.created_at.strftime("%B %d, %Y %I:%M %p"),
            'read': notification.is_read
        })
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@csrf_exempt
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Not found'}, status=404)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_notification_api(request, notification_id):
    if request.method == 'DELETE':
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.delete()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Not found'}, status=404)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_all_notifications_api(request):
    if request.method == 'DELETE':
        Notification.objects.all().delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def edit_notification(request, notification_id):
    """Edit a notification"""
    # Get the notification
    notification = get_object_or_404(Notification, id=notification_id)
    
    # Check permission
    if notification.recipient != request.user and not notification.is_for_all and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this notification.')
        return redirect('my_notifications')
    
    # Get the next URL (where to redirect after saving)
    next_url = request.GET.get('next', request.POST.get('next', 'my_notifications'))
    
    if request.method == 'POST':
        # Store old values for debugging
        old_title = notification.title
        old_message = notification.message
        
        # Update notification fields
        notification.title = request.POST.get('title', notification.title)
        notification.message = request.POST.get('message', notification.message)
        notification.notification_type = request.POST.get('notification_type', notification.notification_type)
        notification.is_for_all = request.POST.get('is_for_all') == 'on'
        
        # FORCE reset read status to make it appear as new
        notification.is_read = False
        notification.is_sent = True
        notification.sent_at = timezone.now()
        
        # Save the notification
        notification.save()
        print(f"Notification updated: {notification.id}")
        print(f"is_read set to: {notification.is_read}")
        
        # Update associated schedule if it exists
        if notification.schedule:
            schedule = notification.schedule
            schedule.title = request.POST.get('title', schedule.title).replace('New Vaccination Schedule: ', '')
            schedule.description = request.POST.get('message', schedule.description)
            schedule.scheduled_date = request.POST.get('scheduled_date', schedule.scheduled_date)
            schedule.start_time = request.POST.get('start_time', schedule.start_time)
            schedule.end_time = request.POST.get('end_time', schedule.end_time)
            schedule.location = request.POST.get('location', schedule.location)
            schedule.address = request.POST.get('address', schedule.address)
            schedule.contact_phone = request.POST.get('contact_phone', schedule.contact_phone)
            schedule.contact_email = request.POST.get('contact_email', schedule.contact_email)
            schedule.target_age_groups = request.POST.get('target_age_groups', schedule.target_age_groups)
            schedule.max_capacity = request.POST.get('max_capacity', schedule.max_capacity)
            schedule.notes = request.POST.get('notes', schedule.notes)
            schedule.is_published = request.POST.get('is_published') == 'on'
            schedule.requires_registration = request.POST.get('requires_registration') == 'on'
            schedule.is_active = request.POST.get('is_active') == 'on'
            schedule.save()
            print(f"Schedule updated: {schedule.id}")
        
        messages.success(request, 'Notification updated successfully! It will appear as new to users.')
        
        # Redirect to the next URL (previous page)
        if next_url and next_url != 'None':
            return redirect(next_url)
        else:
            return redirect('my_notifications')
    
    # GET request - show edit form
    vaccines = Vaccine.objects.filter(is_active=True)
    context = {
        'notification': notification,
        'vaccines': vaccines,
        'next': next_url,
    }
    return render(request, 'edit_notification.html', context)

@login_required
def create_vaccination_record(request):
    """Create a new vaccination record"""
    # Check permission (admin, doctor, or nurse)
    has_permission = False
    
    if request.user.is_staff or request.user.is_superuser:
        has_permission = True
    else:
        try:
            if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type in ['doctor', 'nurse']:
                has_permission = True
        except:
            pass
    
    if not has_permission:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient_id')
            vaccine_id = request.POST.get('vaccine_id')
            dose_number = int(request.POST.get('dose_number', 1))
            total_doses = request.POST.get('total_doses', 1)
            
            if not patient_id or not vaccine_id:
                messages.error(request, 'Patient and Vaccine are required.')
                return redirect('create_vaccination_record')
            
            patient = Patient.objects.get(id=patient_id)
            vaccine = Vaccine.objects.get(id=vaccine_id)
            
            # Convert date strings to date objects
            date_administered_str = request.POST.get('date_administered')
            next_due_date_str = request.POST.get('next_due_date')
            
            # Convert date_administered to date object
            if date_administered_str:
                try:
                    date_administered = datetime.strptime(date_administered_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Invalid date format for administered date. Please use YYYY-MM-DD format.')
                    return redirect('create_vaccination_record')
            else:
                date_administered = None
            
            # Convert next_due_date to date object
            if next_due_date_str and next_due_date_str.strip():
                try:
                    next_due_date = datetime.strptime(next_due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Invalid date format for next due date. Please use YYYY-MM-DD format.')
                    return redirect('create_vaccination_record')
            else:
                next_due_date = None
            
            # Get the logged-in user's name
            if request.user.get_full_name():
                administered_by_name = request.user.get_full_name()
            else:
                administered_by_name = request.user.username
            
            # Check if record exists for this patient and vaccine
            existing_records = VaccinationRecord.objects.filter(
                patient=patient,
                vaccine=vaccine
            ).order_by('-dose_number')
            
            if existing_records.exists():
                # Auto-increment dose number
                highest_dose = existing_records.first().dose_number
                dose_number = highest_dose + 1
                
                record = VaccinationRecord(
                    patient=patient,
                    vaccine=vaccine,
                    dose_number=dose_number,
                    total_doses=total_doses,
                    date_administered=date_administered,
                    next_due_date=next_due_date,
                    administered_by=request.user,  # Store the User object
                    administered_by_name=administered_by_name,  # Store the name as backup
                    administering_facility=request.POST.get('administering_facility') or None,
                    status=request.POST.get('status', 'administered'),
                    reaction=request.POST.get('reaction', 'none'),
                    reaction_notes=request.POST.get('reaction_notes') or None,
                    notes=request.POST.get('notes') or None,
                )
                record.save()
                messages.success(request, f'Dose {dose_number} of {vaccine.name} added successfully for {patient}!')
            else:
                record = VaccinationRecord(
                    patient=patient,
                    vaccine=vaccine,
                    dose_number=dose_number,
                    total_doses=total_doses,
                    date_administered=date_administered,
                    next_due_date=next_due_date,
                    administered_by=request.user,  # Store the User object
                    administered_by_name=administered_by_name,  # Store the name as backup
                    administering_facility=request.POST.get('administering_facility') or None,
                    status=request.POST.get('status', 'administered'),
                    reaction=request.POST.get('reaction', 'none'),
                    reaction_notes=request.POST.get('reaction_notes') or None,
                    notes=request.POST.get('notes') or None,
                )
                record.save()
                messages.success(request, f'First dose of {vaccine.name} added successfully for {patient}!')
            
            return redirect('dashboard')
            
        except Patient.DoesNotExist:
            messages.error(request, 'Selected patient not found.')
            return redirect('create_vaccination_record')
        except Vaccine.DoesNotExist:
            messages.error(request, 'Selected vaccine not found.')
            return redirect('create_vaccination_record')
        except Exception as e:
            messages.error(request, f'Error adding record: {str(e)}')
            print(f"Error creating vaccination record: {e}")
            return redirect('create_vaccination_record')
    
    # GET request - show form
    patients = Patient.objects.all().order_by('first_name', 'last_name')
    vaccines = Vaccine.objects.filter(is_active=True).order_by('name')
    
    context = {
        'patients': patients,
        'vaccines': vaccines,
        'current_user': request.user,
    }
    return render(request, 'vaccination_record_form.html', context)

def view_vaccination_record(request, pk):
    """View a single vaccination record"""
    
    record = get_object_or_404(VaccinationRecord, id=pk)
    
    context = {
        'record': record,
    }
    return render(request, 'view_vaccination_record.html', context)


def edit_vaccination_record(request, pk):
    """Edit a vaccination record"""
    
    record = get_object_or_404(VaccinationRecord, id=pk)
    
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient_id')
            vaccine_id = request.POST.get('vaccine_id')
            dose_number = request.POST.get('dose_number', record.dose_number)
            total_doses = request.POST.get('total_doses', record.total_doses)
            
            if patient_id:
                record.patient = Patient.objects.get(id=patient_id)
            if vaccine_id:
                record.vaccine = Vaccine.objects.get(id=vaccine_id)
            
            record.dose_number = dose_number
            record.total_doses = total_doses
            
            # Convert date strings
            date_administered_str = request.POST.get('date_administered')
            if date_administered_str:
                record.date_administered = datetime.strptime(date_administered_str, '%Y-%m-%d').date()
            
            next_due_date_str = request.POST.get('next_due_date')
            if next_due_date_str and next_due_date_str.strip():
                record.next_due_date = datetime.strptime(next_due_date_str, '%Y-%m-%d').date()
            else:
                record.next_due_date = None
            
            record.administered_by = request.POST.get('administered_by') or None
            record.administering_facility = request.POST.get('administering_facility') or None
            record.status = request.POST.get('status', record.status)
            record.reaction = request.POST.get('reaction', 'none')
            record.reaction_notes = request.POST.get('reaction_notes') or None
            record.notes = request.POST.get('notes') or None
            
            record.save()
            
            messages.success(request, f'Vaccination record updated successfully!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating record: {str(e)}')
            return redirect('edit_vaccination_record', pk=pk)
    
    # GET request - show edit form
    patients = Patient.objects.all().order_by('first_name', 'last_name')
    vaccines = Vaccine.objects.filter(is_active=True).order_by('name')
    
    context = {
        'record': record,
        'patients': patients,
        'vaccines': vaccines,
    }
    return render(request, 'edit_vaccination_record.html', context)


def delete_vaccination_record(request, pk):
    """Delete a vaccination record"""
    
    record = get_object_or_404(VaccinationRecord, id=pk)
    
    if request.method == 'POST':
        patient_name = str(record.patient)
        vaccine_name = record.vaccine.name
        record.delete()
        messages.success(request, f'Vaccination record for {patient_name} ({vaccine_name}) deleted successfully!')
        return redirect('dashboard')
    
    context = {
        'record': record,
    }
    return render(request, 'delete_vaccination_record.html', context)


@login_required
def profile(request):
    """Display user profile information"""
    user = request.user
    
    context = {
        'user': user,
    }
    return render(request, 'profile.html', context)

# ============ SETTINGS VIEWS ============

@login_required
def settings_dashboard(request):
    """Main settings page"""
    user = request.user
    
    # Get current settings from user profile or session
    # Try to get from user profile first
    try:
        if hasattr(user, 'userprofile'):
            theme = user.userprofile.theme if hasattr(user.userprofile, 'theme') else request.session.get('theme', 'light')
            font_size = user.userprofile.font_size if hasattr(user.userprofile, 'font_size') else request.session.get('font_size', 'medium')
            language = user.userprofile.language if hasattr(user.userprofile, 'language') else request.session.get('language', 'en')
        else:
            theme = request.session.get('theme', 'light')
            font_size = request.session.get('font_size', 'medium')
            language = request.session.get('language', 'en')
    except:
        theme = request.session.get('theme', 'light')
        font_size = request.session.get('font_size', 'medium')
        language = request.session.get('language', 'en')
    
    context = {
        'user': user,
        'theme': theme,
        'font_size': font_size,
        'language': language,
    }
    return render(request, 'settings/settings.html', context)


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('settings')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'settings/change_password.html', {'form': form})


@login_required
def update_display_settings(request):
    """Update display settings (theme, font size)"""
    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')
        font_size = request.POST.get('font_size', 'medium')
        
        # Save to session for immediate effect
        request.session['theme'] = theme
        request.session['font_size'] = font_size
        
        # Also save to user profile if available
        try:
            if hasattr(request.user, 'userprofile'):
                request.user.userprofile.theme = theme
                request.user.userprofile.font_size = font_size
                request.user.userprofile.save()
        except:
            pass
        
        messages.success(request, 'Display settings updated successfully!')
        return redirect('settings')
    
    return redirect('settings')


@login_required
def change_language(request):
    """Change interface language"""
    if request.method == 'POST':
        language = request.POST.get('language', 'en')
        
        # Activate language for current session
        activate(language)
        request.session['language'] = language
        request.session['django_language'] = language
        
        # Save to user profile if available
        try:
            if hasattr(request.user, 'userprofile'):
                request.user.userprofile.language = language
                request.user.userprofile.save()
        except:
            pass
        
        messages.success(request, f'Language changed to {dict(settings.LANGUAGES).get(language, language)}')
        return redirect(request.META.get('HTTP_REFERER', 'settings'))
    
    return redirect('settings')


# =============================================
# VAXGUARD — PHASE 3a — MONITORING SESSIONS
# =============================================

from .forms import MonitoringSessionForm


@login_required(login_url='/login/')
def start_monitoring(request, vaccination_id):
    """
    Start a post-vaccination monitoring session.
    Only healthcare workers and admins can start sessions.
    """
    # Role gate
    profile = getattr(request.user, 'userprofile', None)
    if profile is None or profile.user_type not in ('healthcare_worker', 'admin'):
        messages.error(request, 'You do not have permission to start monitoring sessions.')
        return redirect('dashboard')

    vaccination = get_object_or_404(VaccinationRecord, id=vaccination_id)
    patient = vaccination.patient

    # Guard: don't allow two active sessions for the same vaccination
    existing = MonitoringSession.objects.filter(
        vaccination_record=vaccination,
        status='active',
    ).first()
    if existing:
        messages.info(request, 'A monitoring session is already active for this vaccination.')
        return redirect('monitoring_live', session_id=existing.id)

    if request.method == 'POST':
        form = MonitoringSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.vaccination_record = vaccination
            session.patient = patient
            session.started_by = request.user
            session.status = 'active'
            session.current_level = 'green'
            session.save()

            messages.success(
                request,
                f'Monitoring session started for {patient.full_name()}. '
                f'Duration: {session.planned_duration_minutes} minutes.'
            )
            return redirect('monitoring_live', session_id=session.id)
    else:
        default_duration = getattr(vaccination.vaccine, 'monitoring_duration_minutes', 30) or 30
        form = MonitoringSessionForm(initial={
            'planned_duration_minutes': default_duration,
        })

    context = {
        'form': form,
        'vaccination': vaccination,
        'patient': patient,
        'user_status': profile.user_type,
    }
    return render(request, 'start_monitoring.html', context)


@login_required(login_url='/login/')
def monitoring_live(request, session_id):
    """
    Live monitoring view for a session.
    Phase 3b will add real-time streaming; for now shows current state.
    """
    session = get_object_or_404(MonitoringSession, id=session_id)

    # Role gate
    profile = getattr(request.user, 'userprofile', None)
    is_staff_role = profile and profile.user_type in ('healthcare_worker', 'admin')
    is_own_patient = (
        profile and profile.user_type == 'patient'
        and session.patient.user_id == request.user.id
    )
    if not (is_staff_role or is_own_patient):
        messages.error(request, 'You do not have permission to view this session.')
        return redirect('dashboard')

    latest_readings = session.sensor_readings.order_by('-recorded_at')[:20]
    recent_symptoms = session.symptom_reports.select_related('symptom').order_by('-reported_at')[:10]
    latest_assessment = session.risk_assessments.order_by('-assessed_at').first()
    open_alerts = session.alerts.exclude(status='resolved').order_by('-created_at')

    context = {
        'session': session,
        'patient': session.patient,
        'vaccination': session.vaccination_record,
        'latest_readings': latest_readings,
        'recent_symptoms': recent_symptoms,
        'latest_assessment': latest_assessment,
        'open_alerts': open_alerts,
        'user_status': profile.user_type if profile else 'patient',
    }
    return render(request, 'monitoring_live.html', context)


# =============================================
# VAXGUARD — PATIENT + VACCINE STATUS API
# =============================================

@login_required(login_url='/login/')
def patient_vaccine_status_api(request, patient_id, vaccine_id):
    """
    Returns dosing status for a patient + vaccine combination.
    Called by the New Vaccination Record form to auto-populate.
    """
    from .models import VaccineInventory

    patient = get_object_or_404(Patient, id=patient_id)
    vaccine = get_object_or_404(Vaccine, id=vaccine_id)

    requires_total = vaccine.doses_required or 1

    previous = VaccinationRecord.objects.filter(
        patient=patient,
        vaccine=vaccine,
        status='administered',
    ).order_by('-dose_number')

    already_received = previous.count()
    next_dose_number = already_received + 1
    is_complete = already_received >= requires_total
    last_record = previous.first()
    last_date = last_record.date_administered.isoformat() if last_record and last_record.date_administered else None

    inventory = VaccineInventory.objects.filter(vaccine=vaccine).first()
    stock_available = inventory.current_stock if inventory else None
    min_stock = inventory.min_stock_level if inventory else None
    stock_low = (
        stock_available is not None
        and min_stock is not None
        and stock_available <= min_stock
    )
    stock_out = (stock_available == 0) if stock_available is not None else False

    if is_complete:
        message = (
            f"{patient.full_name()} has already received all "
            f"{requires_total} dose(s) of {vaccine.name}."
        )
    else:
        message = f"This will be dose {next_dose_number} of {requires_total}."

    return JsonResponse({
        'requires_total': requires_total,
        'already_received': already_received,
        'next_dose_number': next_dose_number,
        'is_complete': is_complete,
        'last_date': last_date,
        'stock_available': stock_available,
        'min_stock': min_stock,
        'stock_low': stock_low,
        'stock_out': stock_out,
        'message': message,
        'patient_name': patient.full_name(),
        'vaccine_name': vaccine.name,
    })