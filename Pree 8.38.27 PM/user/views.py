from datetime import datetime
import json
import random
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Rental, RentPayment, MaintenanceRequest, RentalLeaseAgreement
from django.db.models import Sum
from django.contrib import messages
from django.contrib.messages import get_messages  
from .forms import UserProfileForm  # You'll need to create this form
from .models import UserProfile  # Add this import
# Update this import line in your views.py file:

# To this (add update_session_auth_hash):
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash

from notification.models import Notification

from django.template.loader import render_to_string

from .models import Property, RentalRequest, PropertyImage

from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect

from .forms import SignupForm, EmailAuthenticationForm, PasswordResetRequestForm

import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse

User = get_user_model()

# Minimum Age for Signup
MIN_AGE = 22

@login_required
def dashboard_view(request):
    if request.user.user_type.lower() == 'home owner':
        return homeowner_dashboard(request)
    else:
       return tenant_dashboard(request)

@login_required
def home_view(request):
    return dashboard_view(request)

@login_required
def homeowner_dashboard(request):
    # Get user's properties with images
    properties = Property.objects.filter(homeowner=request.user).prefetch_related('images')
    
    # Calculate statistics
    property_count = properties.count()
    available_count = properties.filter(is_available=True).count()
    rented_count = properties.filter(is_available=False).count()
    
    # Get all rentals for this homeowner's properties
    rentals = Rental.objects.filter(property__homeowner=request.user)
    
    # Get recent maintenance requests
    maintenance_requests = MaintenanceRequest.objects.filter(
        rental__property__homeowner=request.user
    ).order_by('-request_date')[:5]  # Get the 5 most recent
    
    # Calculate total income from all rent payments
    total_income = 0
    for rental in rentals:
        total_income += RentPayment.objects.filter(rental=rental).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    # Get recent bookings (rentals)
    recent_bookings = rentals.order_by('-start_date')[:5]
    
    # Get pending rental requests
    pending_requests = RentalRequest.objects.filter(
        property__homeowner=request.user,
        status='pending'
    ).order_by('-requested_date')[:5]
    
    notification_count = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).count()
    
    context = {
        'properties': properties,
        'property_count': property_count,
        'rented_count': rented_count,
        'available_count': available_count,
        'total_income': total_income,
        'income_change': -1.5,  # Placeholder - could be calculated from previous period
        'yesterday_income': 9940.00,  # Placeholder
        'last_week_income': 25658.00,  # Placeholder
        'total_expenses': 50000660.00,  # Placeholder
        'expenses_change': 2.5,  # Placeholder
        'yesterday_expenses': 5240.00,  # Placeholder
        'last_week_expenses': 22658.00,  # Placeholder
        'bookings': recent_bookings,
        'maintenance_requests': maintenance_requests,
        'pending_requests': pending_requests,
        'notification_count': notification_count,
        'monthly_earnings_data': json.dumps([
            {'month': 'Jan', 'amount': 5000},
            {'month': 'Feb', 'amount': 7000},
            {'month': 'Mar', 'amount': 6500},
            {'month': 'Apr', 'amount': 8000},
            {'month': 'May', 'amount': 9500},
            {'month': 'Jun', 'amount': 10000},
            {'month': 'Jul', 'amount': 11000},
            {'month': 'Aug', 'amount': 9000},
            {'month': 'Sep', 'amount': 12000},
            {'month': 'Oct', 'amount': 13500},
            {'month': 'Nov', 'amount': 15000},
            {'month': 'Dec', 'amount': 16000}
        ])
    }
    
    return render(request, 'user/dashboard.html', context)

@login_required
def property_list(request):
    properties = Property.objects.filter(homeowner=request.user).prefetch_related('images')
    
    # Calculate statistics
    available_count = properties.filter(is_available=True).count()
    rented_count = properties.filter(is_available=False).count()
    
    # Calculate total income from rentals
    total_income = 0
    rental_properties = Rental.objects.filter(property__homeowner=request.user)
    for rental in rental_properties:
        total_income += RentPayment.objects.filter(rental=rental).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    context = {
        'properties': properties,
        'available_count': available_count,
        'rented_count': rented_count,
        'total_income': total_income
    }
    
    return render(request, 'user/homeowner_properties.html', context)

@login_required
def add_property(request):
    if request.method == 'POST':
        # Handle form submission
        title = request.POST.get('title')
        location = request.POST.get('location')
        property_type = request.POST.get('property_type')
        price = request.POST.get('price')
        bedrooms = request.POST.get('bedrooms')
        bathrooms = request.POST.get('bathrooms')
        description = request.POST.get('description')
        
        property = Property(
            homeowner=request.user,
            title=title,
            location=location,
            property_type=property_type,
            price=price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            description=description
        )
        
        property.save()
        
        # Handle multiple image uploads
        images = request.FILES.getlist('images')  # Use getlist for multiple files
        
        for index, image in enumerate(images):
            PropertyImage.objects.create(
                property=property,
                image=image,
                is_primary=True if index == 0 else False  # First image is primary
            )
        
        messages.success(request, "Property added successfully!")
        return redirect('property_list')
    
    storage = get_messages(request)
    list(storage)  # This consumes and clears all existing messages
    
    return render(request, 'user/add_property.html')

@login_required
def edit_property(request, property_id):
    property = get_object_or_404(Property, id=property_id, homeowner=request.user)
    
    if request.method == 'POST':
        # Handle form submission
        property.title = request.POST.get('title')
        property.location = request.POST.get('location')
        property.property_type = request.POST.get('property_type')
        property.price = request.POST.get('price')
        property.bedrooms = request.POST.get('bedrooms')
        property.bathrooms = request.POST.get('bathrooms')
        property.description = request.POST.get('description')
        property.save()
        
        # Handle new image uploads
        images = request.FILES.getlist('images')
        for index, image in enumerate(images):
            # Check if there's already a primary image
            has_primary = property.images.filter(is_primary=True).exists()
            
            PropertyImage.objects.create(
                property=property,
                image=image,
                is_primary=not has_primary and index == 0  # Set first new image as primary only if no primary exists
            )
            
        messages.success(request, "Property updated successfully!")
        return redirect('property_list')
    
    return render(request, 'user/edit_property.html', {'property': property})

@login_required
def delete_property(request, property_id):
    property = get_object_or_404(Property, id=property_id, homeowner=request.user)
    
    if request.method == 'POST':
        property.delete()
        messages.success(request, "Property deleted successfully!")
        return redirect('property_list')
    
    return render(request, 'user/delete_property.html', {'property': property})

# New image management views
@login_required
def delete_property_image(request, image_id):
    image = get_object_or_404(PropertyImage, id=image_id, property__homeowner=request.user)
    property_id = image.property.id
    was_primary = image.is_primary
    image.delete()
    
    # If we deleted the primary image, make the first remaining image primary
    if was_primary:
        first_image = PropertyImage.objects.filter(property_id=property_id).first()
        if first_image:
            first_image.is_primary = True
            first_image.save()
    
    messages.success(request, "Image deleted successfully!")
    return redirect('edit_property', property_id=property_id)

@login_required
def set_primary_image(request, image_id):
    image = get_object_or_404(PropertyImage, id=image_id, property__homeowner=request.user)
    
    # Set all other images as non-primary
    PropertyImage.objects.filter(property=image.property).update(is_primary=False)
    
    # Set this image as primary
    image.is_primary = True
    image.save()
    
    messages.success(request, "Primary image updated successfully!")
    return redirect('edit_property', property_id=image.property.id)

# Placeholder views for other dashboard features
@login_required
def booking_list(request):
    if request.user.user_type == 'home owner':
        # Get all active rentals for this homeowner's properties
        rentals = Rental.objects.filter(
            property__homeowner=request.user,
            is_active=True
        ).select_related('property', 'tenant').prefetch_related('property__images')
        
        # Get approved rental requests awaiting lease signature
        pending_leases = RentalRequest.objects.filter(
            property__homeowner=request.user,
            status='approved'
        ).exclude(
            rental_lease_agreement__rental__isnull=False
        ).select_related('property', 'tenant', 'rental_lease_agreement').prefetch_related('property__images')
        
        # Create combined data
        rental_data = []
        
        # Add existing rentals
        for rental in rentals:
            current_month = timezone.now().replace(day=1)
            payment = RentPayment.objects.filter(
                rental=rental,
                month=current_month
            ).first()
            
            lease_agreement = getattr(rental, 'rental_lease_agreement', None)
            
            rental_data.append({
                'id': rental.id,
                'property': rental.property,
                'tenant': rental.tenant,
                'start_date': rental.start_date,
                'end_date': rental.end_date,  # Ensure this is included
                'monthly_rent': rental.rent_amount,
                'status': 'active',
                'payment_status': 'paid' if payment and payment.is_paid else 'pending',
                'payment': payment,
                'lease_signed': True,
                'is_rental': True,
                'type': 'rental'
            })
        
        # Add approved requests waiting for lease signature
        for pending_request in pending_leases:
            lease = getattr(pending_request, 'rental_lease_agreement', None)
            
            rental_data.append({
                'id': pending_request.id,
                'property': pending_request.property,
                'tenant': pending_request.tenant,
                'start_date': pending_request.start_date,
                'end_date': pending_request.end_date,  # Include end date from rental request
                'monthly_rent': pending_request.property.price,
                'status': 'pending_lease',
                'payment_status': 'n/a',
                'payment': None,
                'lease_signed': False,
                'is_rental': False,
                'lease_agreement': lease,
                'type': 'rental_request'
            })
        
        context = {
            'bookings': rental_data,
            'is_homeowner': True
        }
    else:
        # For tenants - make sure to include end_date here too
        rentals = Rental.objects.filter(tenant=request.user, is_active=True).prefetch_related('property__images')
        booking_data = []
        for rental in rentals:
            booking_data.append({
                'id': rental.id,
                'property': rental.property,
                'tenant': rental.tenant,
                'start_date': rental.start_date,
                'end_date': rental.end_date,
                'rent_amount': rental.rent_amount,
                'is_active': rental.is_active
            })
        context = {
            'bookings': booking_data,
            'is_homeowner': False
        }
    
    return render(request, 'user/booking_list.html', context)

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count()
    }

    return render(request, 'user/notifications.html', context) 

@login_required
def payment_details(request):
    return render(request, 'user/payment_details.html')

@login_required
def transactions(request):
    return render(request, 'user/transactions.html')

@login_required
def report(request):
    return render(request, 'user/report.html')

# Generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Send OTP via Email
def send_otp_email(email, otp):
    subject = "Your OTP for Signup/Login"
    message = f"Your OTP is {otp}. This OTP is valid for 5 minutes."
    from_email = "noreply@yourdomain.com"
    send_mail(subject, message, from_email, [email], fail_silently=False)

# Signup with Age Validation
@csrf_protect
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)

                # Validate Age
                date_of_birth = form.cleaned_data.get('date_of_birth')
                if date_of_birth:
                    today = datetime.today().date()
                    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
                    if age < MIN_AGE:
                        messages.error(request, "You must be at least 22 years old to sign up.")
                        return render(request, 'user/signup.html', {'form': form})

                user.save()
                messages.success(request, "Your account has been created successfully. You can now log in.")
                return redirect('login')
            except Exception as e:
                print(f"Error saving user: {str(e)}")
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        form = SignupForm()
    
    return render(request, 'user/signup.html', {'form': form})

# OTP Verification for Signup
def verify_otp_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        entered_otp = request.POST.get('otp')
        cached_otp = cache.get(f"otp_{email}")

        if cached_otp and cached_otp == entered_otp:
            signup_data = request.session.get('signup_data')
            if signup_data:
                if 'date_of_birth' in signup_data:
                    signup_data['date_of_birth'] = datetime.fromisoformat(signup_data['date_of_birth']).date()

                user = User.objects.create_user(
                    username=signup_data['username'],
                    email=signup_data['email'],
                    phone_number=signup_data['phone_number'],
                    address=signup_data['address'],
                    company_name=signup_data['company_name'],
                    date_of_birth=signup_data['date_of_birth'],
                    user_type=signup_data['user_type'],
                    password=signup_data['password1'],
                )
                del request.session['signup_data']
                messages.success(request, "Account created successfully! You can now log in.")
                return redirect('login')
            else:
                messages.error(request, "Session expired. Please try signing up again.")
                return redirect('signup')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'user/verify_otp.html')

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

# Login with OTP, but skip OTP if the user has logged in within 3 hours
def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(data=request.POST)
        email = request.POST.get('email')
        password = request.POST.get('password')

        if form.is_valid():
            user = authenticate(request, email=email, password=password)

            if user:
                last_otp_verified_time = cache.get(f"last_otp_verified_{email}")

                print("Here 1")

                # Check if the last OTP verification was within the last 3 hours
                if last_otp_verified_time and (timezone.now() - last_otp_verified_time).total_seconds() < 3 * 3600:
                    # Directly log in the user without OTP
                    print("Here 2")

                    login(request, user)
                    request.session['user_id'] = user.id
                    request.session['user_email'] = user.email
                    request.session['user_type'] = user.user_type
                    request.session.set_expiry(3600)  # Session expires in 1 hour

                    messages.success(request, "Login successful!")
                    return redirect('dashboard')

                # Otherwise, generate OTP and ask for verification
                otp = generate_otp()
                cache.set(f"otp_{email}", otp, timeout=300)
                send_otp_email(email, otp)

                print("Here 3")

                request.session['login_email'] = email
                request.session['login_password'] = password

                messages.info(request, f"An OTP has been sent to {email}. Please enter it to complete login.")
                return redirect('login_verify_otp')
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()
    return render(request, 'user/login.html', {'form': form})

def login_verify_otp_view(request):
    if request.method == 'POST':
        email = request.session.get('login_email')
        password = request.session.get('login_password')
        entered_otp = request.POST.get('otp')

        cached_otp = cache.get(f"otp_{email}")

        if cached_otp and cached_otp == entered_otp:
            # Manually fetch the user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "No account found with this email.")
                return redirect('login')

            # Check if the password is correct
            if user.check_password(password):
                login(request, user)

                # Store session data
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_type'] = user.user_type
                request.session.set_expiry(3600)  # Session expires in 1 hour

                # Store last OTP verification time to bypass OTP for the next 3 hours
                cache.set(f"last_otp_verified_{email}", timezone.now(), timeout=3 * 3600)

                messages.success(request, "Login successful!")
                del request.session['login_email']
                del request.session['login_password']
                return redirect('dashboard')  # Redirect to dashboard
            else:
                messages.error(request, "Authentication failed. Please try again.")
                return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'user/login_verify_otp.html')

# Logout and Clear Session
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')  # Redirect to login page after logout

def landing_page(request):
    return render(request, 'user/landing.html')

def about_page(request):
    return render(request, 'user/about.html')

def service_page(request):
    return render(request, 'user/service.html')

def properties_list(request):
    """View to list all properties with filtering and featured properties."""
    # Only get properties that are marked as featured
    featured_properties = Property.objects.filter(featured=True).prefetch_related('images')
    
    # Get all properties for the main list
    all_properties = Property.objects.all().prefetch_related('images')

    # Filtering
    location = request.GET.get('location', '')
    property_type = request.GET.get('property_type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    if location:
        all_properties = all_properties.filter(location__icontains=location)
    if property_type:
        all_properties = all_properties.filter(property_type=property_type)
    if min_price:
        all_properties = all_properties.filter(price__gte=min_price)
    if max_price:
        all_properties = all_properties.filter(price__lte=max_price)

    return render(request, 'user/properties_list.html', {
        'featured_properties': featured_properties,
        'all_properties': all_properties,
    })

def property_detail(request, pk):
    """View to show details of a single property."""
    property = get_object_or_404(Property.objects.prefetch_related('images'), pk=pk)
    return render(request, 'user/property_detail.html', {'property': property})

def view_property_detail(request, pk):
    """View to show details of a single property."""
    property = get_object_or_404(Property.objects.prefetch_related('images'), pk=pk)
    return render(request, 'user/view_property.html', {'property': property})

def password_reset_request_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = get_user_model().objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(str(user.pk).encode())

                # Send password reset email
                reset_url = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')

                subject = 'Password Reset Request'
                message = render_to_string('user/password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                })

                send_mail(subject, message, 'noreply@yourdomain.com', [email])

                messages.success(request, "A password reset link has been sent to your email.")
                return redirect('login')
            except get_user_model().DoesNotExist:
                messages.error(request, "No user found with this email address.")
                return redirect('password_reset_request')
        else:
            messages.error(request, "Please provide a valid email address.")
    else:
        form = PasswordResetRequestForm()

    return render(request, 'user/password_reset_request.html', {'form': form})

def password_reset_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Your password has been reset successfully. You can now log in.")
                    return redirect('login')
            else:
                form = SetPasswordForm(user)

            return render(request, 'user/password_reset.html', {'form': form})
        else:
            messages.error(request, "The reset link is invalid or expired.")
            return redirect('password_reset_request')
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        messages.error(request, "The reset link is invalid or expired.")
        return redirect('password_reset_request')

@login_required
def tenant_dashboard(request):
    user = request.user

    # Active rentals
    rentals = Rental.objects.filter(tenant=user, is_active=True).select_related('property').prefetch_related('property__images')

    # Total rent paid
    total_paid = RentPayment.objects.filter(rental__tenant=user, is_paid=True).aggregate(
        total=Sum('amount_paid'))['total'] or 0

    # Next rent due
    next_due_payment = RentPayment.objects.filter(
        rental__tenant=user, is_paid=False, month__gte=timezone.now().date()
    ).order_by('month').first()

    # Maintenance requests (limit to 3)
    maintenance_requests = MaintenanceRequest.objects.filter(
        rental__tenant=user
    ).select_related('rental').order_by('-request_date')[:3]

    context = {
        'rentals': rentals,
        'rental_count': rentals.count(),
        'total_paid': total_paid,
        'next_due': {
            'amount': next_due_payment.amount_paid if next_due_payment else 0,
            'date': next_due_payment.month if next_due_payment else None,
        },
        'notification_count': Notification.objects.filter(user=request.user, is_read=False).count(),  # Update with real logic later
        'requests': maintenance_requests
    }

    return render(request, 'user/tenant_dashboard.html', context)

@login_required
def tenant_property_list(request):
    if request.user.user_type != 'tenant':
        return redirect('dashboard')

    properties = Property.objects.filter(is_available=True).prefetch_related('images')
    return render(request, 'user/available_properties.html', {'properties': properties})

@login_required
def rent_property(request, property_id):
    if request.user.user_type != 'tenant':
        return redirect('dashboard')

    properties = get_object_or_404(Property.objects.prefetch_related('images'), pk=property_id, is_available=True)

    if request.method == 'POST':
        message = request.POST.get('message', '')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date', None)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid start date format.")
            return redirect('rent_property', property_id=property_id)

        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid end date format.")
                return redirect('rent_property', property_id=property_id)

        if end_date and end_date < start_date:
            messages.error(request, "End date must be after start date.")
            return redirect('rent_property', property_id=property_id)

        RentalRequest.objects.create(
            tenant=request.user,
            property=properties,
            start_date=start_date,
            end_date=end_date,
            message=message,
            status='pending'
        )

        Notification.objects.create(
            user=properties.homeowner,
            message=f"New rental request from {request.user.get_full_name() or request.user.email} for {properties.title}",
            is_read=False
        )

        messages.success(request, f"Your rental request for {properties.title} has been submitted and is awaiting approval from the homeowner.")
        return redirect('my_rental_requests')

    return render(request, 'user/rent_property_confirm.html', {'property': properties})

@login_required
def my_rental_requests(request):
    """View for tenants to see their rental requests"""
    if request.user.user_type != 'tenant':
        return redirect('dashboard')
        
    rental_requests = RentalRequest.objects.filter(tenant=request.user).order_by('-requested_date').prefetch_related('property__images')
    return render(request, 'user/my_rental_requests.html', {'rental_requests': rental_requests})

@login_required
def my_rentals(request):
    """View for tenants to see their active rentals"""
    if request.user.user_type != 'tenant':
        return redirect('dashboard')
        
    rentals = Rental.objects.filter(tenant=request.user).select_related('property__homeowner').prefetch_related('property__images')

    for rent in rentals:
        # Last payment
        last_payment = RentPayment.objects.filter(rental=rent, is_paid=True).order_by('-paid_on').first()
        rent.last_paid_date = last_payment.paid_on if last_payment else None

        # Calculate next due date (e.g., assume monthly rent)
        if last_payment:
            rent.next_payment_date = last_payment.paid_on + timezone.timedelta(days=30)
        else:
            rent.next_payment_date = rent.start_date + timezone.timedelta(days=30)

    return render(request, 'user/my_rentals.html', {'rentals': rentals})

@login_required
def manage_rental_requests(request):
    """View for homeowners to manage incoming rental requests"""
    if request.user.user_type != 'home owner':
        return redirect('dashboard')
        
    rental_requests = RentalRequest.objects.filter(
        property__homeowner=request.user
    ).order_by('-requested_date').prefetch_related('property__images')
    
    return render(request, 'user/manage_rental_requests.html', {'rental_requests': rental_requests})

@login_required
def rent_payments(request):
    if request.user.user_type != 'tenant':
        return redirect('dashboard')

    payments = RentPayment.objects.filter(rental__tenant=request.user).order_by('-month')
    return render(request, 'user/rent_payments.html', {'payments': payments})



# Stripe keys defined directly (Not recommended for production)
STRIPE_SECRET_KEY = 'sk_test_51RMYq6FJTmACrmbBHTIN9zYr4l9uWXwUKmUxQLuAdtBQqeDRErcQMr6it3emXSZLC5nogtKF07dK5g382ieF5yRT009okBxrBy'
STRIPE_PUBLISHABLE_KEY = 'pk_test_51RMYq6FJTmACrmbBIWHfWrhNNueqwec5lWjoHqNNSewjGpsDtLUMvbR5KjGdaJP5IYM3GJylnu1ruqH6oWWHkDFz00GPOhw69h'

stripe.api_key = STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request, rental_id):
   rental = get_object_or_404(Rental, id=rental_id, tenant=request.user)
   amount = int(rental.rent_amount * 100)  # Convert to paisa

   session = stripe.checkout.Session.create(
       payment_method_types=['card'],
       line_items=[{
           'price_data': {
               'currency': 'npr',
               'product_data': {
                   'name': f'Rent for {rental.property.title}',
               },
               'unit_amount': amount,
           },
           'quantity': 1,
       }],
       mode='payment',
       success_url=request.build_absolute_uri('/tenant/payment-success/') + '?session_id={CHECKOUT_SESSION_ID}',
       cancel_url=request.build_absolute_uri('/tenant/payment-cancel/'),
       metadata={
           'rental_id': str(rental.id),
           'tenant_email': request.user.email,
       }
   )

   return JsonResponse({'id': session.id, 'stripe_public_key': STRIPE_PUBLISHABLE_KEY})

@csrf_exempt
def stripe_webhook(request):
   payload = request.body
   sig_header = request.META['HTTP_STRIPE_SIGNATURE']
   endpoint_secret = 'your_webhook_signing_secret'

   try:
       event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
   except stripe.error.SignatureVerificationError:
       return HttpResponse(status=400)

   if event['type'] == 'checkout.session.completed':
       session = event['data']['object']
       rental_id = session['metadata']['rental_id']

       rental = Rental.objects.get(id=rental_id)
       RentPayment.objects.create(
           rental=rental,
           month=timezone.now(),
           amount_paid=session['amount_total'] / 100,
           is_paid=True
       )

   return HttpResponse(status=200)

@login_required
@csrf_exempt
def payment_success(request):
   session_id = request.GET.get("session_id")
   if session_id:
       session = stripe.checkout.Session.retrieve(session_id)
       rental_id = session.metadata.get('rental_id')

       rental = Rental.objects.get(id=rental_id)
       
       # Add the month field - using the current month as an example
       current_month = timezone.now().replace(day=1)
       
       RentPayment.objects.create(
           rental=rental,
           month=current_month,  # Added the missing month field
           amount_paid=session.amount_total / 100,
           is_paid=True,
           paid_on=timezone.now()
       )

   return render(request, 'user/payment_success.html')

@login_required
def payment_cancel(request):
   return render(request, 'user/payment_cancel.html')

@login_required
def tenant_payment_history(request):
   payments = RentPayment.objects.filter(
       rental__tenant=request.user, is_paid=True
   ).order_by('-paid_on')

   return render(request, 'user/payment_history.html', {'payments': payments})

from .forms import MaintenanceRequestForm

@login_required
def submit_maintenance_request(request, rental_id):
   rental = get_object_or_404(Rental, id=rental_id, tenant=request.user)

   if request.method == 'POST':
       form = MaintenanceRequestForm(request.POST, request.FILES)
       if form.is_valid():
           try:
               maintenance_request = form.save(commit=False)
               maintenance_request.rental = rental
               maintenance_request.status = 'pending'
               
               # Check if an attachment is provided and validate it's an image
               if 'attachment' in request.FILES:
                   attachment = request.FILES['attachment']
                   # Check file extension
                   ext = attachment.name.split('.')[-1].lower()
                   if ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']:
                       messages.error(request, "Only image files are allowed for attachments.")
                       return render(request, 'user/submit_request.html', {
                           'form': form,
                           'rental': rental
                       })
               
               maintenance_request.save()
               messages.success(request, 'Maintenance request submitted successfully.')
               return redirect('view_maintenance_requests')
           except Exception as e:
               messages.error(request, f"Error submitting request: {str(e)}")
       else:
           for field, errors in form.errors.items():
               for error in errors:
                   messages.error(request, f"{field}: {error}")
   else:
       form = MaintenanceRequestForm()

   return render(request, 'user/submit_request.html', {
       'form': form,
       'rental': rental
   })

@login_required
def view_maintenance_requests(request):
   requests = MaintenanceRequest.objects.filter(
       rental__tenant=request.user
   ).select_related('rental').order_by('-request_date')

   return render(request, 'user/maintenance_list.html', {
       'requests': requests
   })

@login_required
def owner_maintenance_requests(request):
   """
   View for homeowners to see maintenance requests for their properties.
   Includes filtering by property, status, and priority.
   """
   if request.user.user_type != 'home owner':
       messages.error(request, "You don't have permission to view this page.")
       return redirect('dashboard')
   
   # Get all properties owned by this user
   properties = Property.objects.filter(homeowner=request.user)
   property_ids = properties.values_list('id', flat=True)
   
   # Get all rentals for these properties
   rentals = Rental.objects.filter(property__id__in=property_ids)
   
   # Filter requests
   requests_queryset = MaintenanceRequest.objects.filter(rental__in=rentals)
   
   # Apply filters from GET parameters
   property_filter = request.GET.get('property')
   status_filter = request.GET.get('status')
   priority_filter = request.GET.get('priority')
   
   if property_filter:
       requests_queryset = requests_queryset.filter(rental__property__id=property_filter)
   
   if status_filter:
       requests_queryset = requests_queryset.filter(status=status_filter)
   
   if priority_filter:
       requests_queryset = requests_queryset.filter(priority=priority_filter)
   
   # Order by date (newest first)
   requests_queryset = requests_queryset.order_by('-request_date')
   
   # Pagination
   paginator = Paginator(requests_queryset, 10)  # 10 requests per page
   page = request.GET.get('page')
   
   try:
       requests = paginator.page(page)
   except PageNotAnInteger:
       requests = paginator.page(1)
   except EmptyPage:
       requests = paginator.page(paginator.num_pages)
   
   context = {
       'requests': requests,
       'properties': properties,
       'selected_property': property_filter,
       'status': status_filter,
       'priority': priority_filter
   }
   
   return render(request, 'owner/maintenance_list.html', context)

@login_required
def maintenance_request_detail(request, request_id):
   """
   Detailed view of a single maintenance request for homeowners.
   """
   if request.user.user_type != 'home owner':
       messages.error(request, "You don't have permission to view this page.")
       return redirect('dashboard')
   
   # Get the maintenance request and verify ownership
   maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
   
   # Check if this is the owner of the property
   if maintenance_request.rental.property.homeowner != request.user:
       messages.error(request, "You don't have permission to view this maintenance request.")
       return redirect('owner_maintenance_requests')
   
   context = {
       'request': maintenance_request
   }
   
   return render(request, 'owner/maintenance_detail.html', context)

@login_required
def update_maintenance_request(request, request_id):
   """
   Update the status and notes of a maintenance request.
   """
   if request.user.user_type != 'home owner':
       messages.error(request, "You don't have permission to perform this action.")
       return redirect('dashboard')
   
   # Get the maintenance request and verify ownership
   maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
   
   # Check if this is the owner of the property
   if maintenance_request.rental.property.homeowner != request.user:
       messages.error(request, "You don't have permission to update this maintenance request.")
       return redirect('owner_maintenance_requests')
   
   if request.method == 'POST':
       status = request.POST.get('status')
       admin_notes = request.POST.get('admin_notes')
       resolved_by = request.POST.get('resolved_by')
       
       # Update the request
       maintenance_request.status = status
       maintenance_request.admin_notes = admin_notes
       
       # If status changed to resolved, set the resolved date and who resolved it
       if status == 'resolved' and maintenance_request.resolved_date is None:
           maintenance_request.resolved_date = timezone.now()
           maintenance_request.is_resolved = True
           maintenance_request.resolved_by = resolved_by
       
       # If status changed from resolved, clear the resolved date
       if status != 'resolved':
           maintenance_request.is_resolved = False
       
       maintenance_request.save()
       
       messages.success(request, "Maintenance request updated successfully.")
       
   return redirect('maintenance_request_detail', request_id=request_id)

@login_required
def update_maintenance_status(request, request_id):
   """
   Quick update of maintenance request status from the list view.
   """
   if request.user.user_type != 'home owner':
       messages.error(request, "You don't have permission to perform this action.")
       return redirect('dashboard')
   
   # Get the maintenance request and verify ownership
   maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
   
   # Check if this is the owner of the property
   if maintenance_request.rental.property.homeowner != request.user:
       messages.error(request, "You don't have permission to update this maintenance request.")
       return redirect('owner_maintenance_requests')
   
   if request.method == 'POST':
       status = request.POST.get('status')
       
       # Update the request
       maintenance_request.status = status
       
       # If status changed to resolved, set the resolved date
       if status == 'resolved' and maintenance_request.resolved_date is None:
           maintenance_request.resolved_date = timezone.now()
           maintenance_request.is_resolved = True
           maintenance_request.resolved_by = request.user.get_full_name() or request.user.username
       
       # If status changed from resolved, clear the resolved date
       if status != 'resolved':
           maintenance_request.is_resolved = False
       
       maintenance_request.save()
       
       messages.success(request, f"Maintenance request marked as {status}.")
   
   return redirect('owner_maintenance_requests')

@login_required
def rental_request_detail(request, request_id):
   """View for homeowners to view details of a rental request"""
   if request.user.user_type != 'home owner':
       return redirect('dashboard')
       
   rental_request = get_object_or_404(
       RentalRequest,
       id=request_id,
       property__homeowner=request.user
   )
   
   return render(request, 'user/rental_request_detail.html', {'rental_request': rental_request})

@login_required
def rental_request_action(request, request_id):
   """View for homeowners to approve or reject rental requests"""
   if request.user.user_type != 'home owner':
       return redirect('dashboard')
       
   rental_request = get_object_or_404(
       RentalRequest,
       id=request_id,
       property__homeowner=request.user,
       status='pending'
   )
   
   if request.method == 'POST':
       action = request.POST.get('action')
       
       if action == 'approve':
           # Approve the request
           rental_request.status = 'approved'
           rental_request.save()
           
           # Check if a lease agreement already exists
           if not hasattr(rental_request, 'rental_lease_agreement'):
               # Create a rental lease agreement
               lease_text = f"""
LEASE AGREEMENT

This lease agreement is entered into between:

LANDLORD: {request.user.get_full_name() or request.user.email}
TENANT: {rental_request.tenant.get_full_name() or rental_request.tenant.email}

PROPERTY DETAILS:
Property: {rental_request.property.title}
Address: {rental_request.property.location}
Type: {rental_request.property.get_property_type_display()}

LEASE TERMS:
Monthly Rent: NPR {rental_request.property.price}
Start Date: {rental_request.start_date}
End Date: {rental_request.end_date if rental_request.end_date else 'Not specified'}

TERMS AND CONDITIONS:
1. The tenant agrees to pay rent on or before the 5th of each month
2. The tenant shall maintain the property in good condition
3. The tenant shall not sublet the property without written permission
4. Either party may terminate this lease with 30 days written notice

By signing below, both parties agree to the terms of this lease agreement.
               """
               
               RentalLeaseAgreement.objects.create(
                   rental_request=rental_request,
                   lease_text=lease_text
               )
           
           # Notify tenant to sign lease
           Notification.objects.create(
               user=rental_request.tenant,
               message=f"Your rental request for {rental_request.property.title} has been approved! Please sign the lease agreement to proceed.",
               is_read=False
           )
           
           messages.success(request, f"Rental request approved. Waiting for tenant to sign the lease agreement.")
       
       elif action == 'reject':
           rental_request.status = 'rejected'
           rental_request.save()
           messages.info(request, f"You have rejected the rental request from {rental_request.tenant.email}.")
       
       return redirect('manage_rental_requests')
   
   return render(request, 'user/rental_request_detail.html', {'rental_request': rental_request})

# New views for lease management
@login_required
def tenant_pending_leases(request):
   """View for tenants to see lease agreements waiting for signature"""
   if request.user.user_type != 'tenant':
       return redirect('dashboard')
   
   pending_leases = RentalLeaseAgreement.objects.filter(
       rental_request__tenant=request.user,
       tenant_signed=False,
       rental_request__status='approved'
   ).order_by('-created_at')
   
   return render(request, 'user/tenant_pending_leases.html', {
       'pending_leases': pending_leases
   })

@login_required
def sign_rental_lease(request, lease_id):
   """View for tenant to sign rental lease agreement"""
   if request.user.user_type != 'tenant':
       return redirect('dashboard')
   
   lease = get_object_or_404(
       RentalLeaseAgreement,
       id=lease_id,
       rental_request__tenant=request.user,
       tenant_signed=False
   )
   
   if request.method == 'POST':
       signature = request.POST.get('signature')
       
       # Check if signature is provided
       if not signature:
           messages.error(request, "Please provide your signature.")
           return render(request, 'user/sign_rental_lease.html', {'lease': lease})
       
       # Handle ID uploads
       id_front = request.FILES.get('id_front')
       id_back = request.FILES.get('id_back')
       
       # Validate ID uploads (optional but recommended)
       if id_front:
           # Check file extension
           ext = id_front.name.split('.')[-1].lower()
           if ext not in ['jpg', 'jpeg', 'png', 'pdf']:
               messages.error(request, "Only JPG, PNG, and PDF files are allowed for ID uploads.")
               return render(request, 'user/sign_rental_lease.html', {'lease': lease})
       
       if id_back:
           # Check file extension
           ext = id_back.name.split('.')[-1].lower()
           if ext not in ['jpg', 'jpeg', 'png', 'pdf']:
               messages.error(request, "Only JPG, PNG, and PDF files are allowed for ID uploads.")
               return render(request, 'user/sign_rental_lease.html', {'lease': lease})
       
       # Update lease agreement
       lease.tenant_signed = True
       lease.tenant_signature = signature
       lease.tenant_signed_at = timezone.now()
       
       # Save ID uploads
       if id_front:
           lease.tenant_id_front = id_front
       if id_back:
           lease.tenant_id_back = id_back
       
       lease.save()
       
       # Create the actual rental now that lease is signed
       rental = Rental.objects.create(
           tenant=lease.rental_request.tenant,
           property=lease.rental_request.property,
           rent_amount=lease.rental_request.property.price,
           start_date=lease.rental_request.start_date,
           end_date=lease.rental_request.end_date,
           is_active=True
       )
       
       lease.rental = rental
       lease.save()
       
       # Update property availability
       lease.rental_request.property.is_available = False
       lease.rental_request.property.save()
       
       # Notify homeowner
       notification_message = f"Lease agreement signed by {request.user.email} for {lease.rental_request.property.title}"
       if id_front or id_back:
           notification_message += " (ID documents uploaded)"
       
       Notification.objects.create(
           user=lease.rental_request.property.homeowner,
           message=notification_message,
           is_read=False
       )
       
       messages.success(request, "Lease agreement signed successfully! Your rental is now active.")
       return redirect('my_rentals')
   
   return render(request, 'user/sign_rental_lease.html', {'lease': lease})

@login_required
def view_rental_lease(request, lease_id):
   """View to display rental lease agreement"""
   lease = get_object_or_404(RentalLeaseAgreement, id=lease_id)
   
   # Check if user has permission to view this lease
   if request.user != lease.rental_request.tenant and request.user != lease.rental_request.property.homeowner:
       messages.error(request, "You don't have permission to view this lease.")
       return redirect('dashboard')
   
   return render(request, 'user/view_rental_lease.html', {'lease': lease})

@login_required
def tenant_signed_leases(request):
   """View for tenants to see their signed lease agreements"""
   if request.user.user_type != 'tenant':
       return redirect('dashboard')
   
   signed_leases = RentalLeaseAgreement.objects.filter(
       rental_request__tenant=request.user,
       tenant_signed=True
   ).order_by('-tenant_signed_at')
   
   return render(request, 'user/tenant_signed_leases.html', {
       'signed_leases': signed_leases
   })

@login_required
def homeowner_signed_leases(request):
   """View for homeowners to see signed lease agreements for their properties"""
   if request.user.user_type != 'home owner':
       return redirect('dashboard')
   
   signed_leases = RentalLeaseAgreement.objects.filter(
       rental_request__property__homeowner=request.user,
       tenant_signed=True,
       homeowner_signed=True
   ).order_by('-tenant_signed_at')
   
   return render(request, 'user/homeowner_signed_leases.html', {
       'signed_leases': signed_leases
   })

@login_required
def homeowner_pending_leases(request):
   """View for homeowners to see pending lease signatures"""
   if request.user.user_type != 'home owner':
       return redirect('dashboard')
   
   # Fetch all leases for this homeowner's approved rental requests
   pending_leases = RentalLeaseAgreement.objects.filter(
       rental_request__property__homeowner=request.user,
       rental_request__status='approved',
       tenant_signed=True,  # ✅ Only include if tenant has signed
       homeowner_signed=False
   ).exclude(
       tenant_signed=True,
       homeowner_signed=True
   ).order_by('-created_at')
   
   return render(request, 'user/homeowner_pending_leases.html', {
       'pending_leases': pending_leases
   })

@login_required
def homeowner_sign_lease(request, lease_id):
   """View for homeowner to sign lease agreement"""
   if request.user.user_type != 'home owner':
       return redirect('dashboard')
   
   lease = get_object_or_404(
       RentalLeaseAgreement,
       id=lease_id,
       rental_request__property__homeowner=request.user,
       homeowner_signed=False
   )
   
   if request.method == 'POST':
       signature = request.POST.get('signature')
       
       if signature:
           lease.homeowner_signed = True
           lease.homeowner_signature = signature
           lease.homeowner_signed_at = timezone.now()
           lease.save()
           
           # If both parties have signed, activate the rental
           if lease.tenant_signed and lease.homeowner_signed:
               # Update property availability
               lease.rental_request.property.is_available = False
               lease.rental_request.property.save()
               
               # Notify tenant that lease is fully executed
               Notification.objects.create(
                   user=lease.rental_request.tenant,
                   message=f"Lease agreement for {lease.rental_request.property.title} has been fully executed by both parties.",
                   is_read=False
               )
           
           messages.success(request, "Lease agreement signed successfully!")
           return redirect('view_rental_lease', lease_id=lease.id)
       else:
           messages.error(request, "Please provide your signature.")
   
   return redirect('view_rental_lease', lease_id=lease.id)

@login_required
def terminate_lease(request, rental_id):
   if request.user.user_type != 'home owner':
       messages.error(request, "You are not authorized to perform this action.")
       return redirect('dashboard')

   rental = get_object_or_404(Rental, id=rental_id, property__homeowner=request.user)
   
   if request.method == 'POST':
       rental.delete()
       messages.success(request, "Rental lease has been permanently terminated.")
   
   return redirect('booking_list')

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
@login_required
def mark_notification_read(request):
   notification_id = request.POST.get("id")
   try:
       notification = Notification.objects.get(id=notification_id, user=request.user)
       notification.is_read = True
       notification.save()
       return JsonResponse({'status': 'success'})
   except Notification.DoesNotExist:
       return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)

@require_POST
@login_required
def mark_all_notifications_read(request):
   Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
   return JsonResponse({'status': 'success'})

@login_required
def homeowner_payment_history(request):
    """View for homeowners to see all payments received"""
    if request.user.user_type != 'home owner':
        return redirect('dashboard')
    
    # Get all properties owned by this user
    properties = Property.objects.filter(homeowner=request.user)
    
    # Get all rentals for these properties
    rentals = Rental.objects.filter(property__in=properties)
    
    # Get all payments for these rentals
    payments = RentPayment.objects.filter(
        rental__in=rentals,
        is_paid=True
    ).select_related(
        'rental__property',
        'rental__tenant'
    ).order_by('-paid_on')
    
    # Calculate total income
    total_income = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    # Get unique tenants for filter
    unique_tenants = User.objects.filter(
        id__in=rentals.values_list('tenant__id', flat=True).distinct()
    )
    
    # Apply filters
    property_filter = request.GET.get('property')
    tenant_filter = request.GET.get('tenant')
    month_filter = request.GET.get('month')
    
    if property_filter:
        payments = payments.filter(rental__property__id=property_filter)
    
    if tenant_filter:
        payments = payments.filter(rental__tenant__id=tenant_filter)
    
    if month_filter:
        payments = payments.filter(month__month=month_filter)
    
    context = {
        'payments': payments,
        'total_income': total_income,
        'properties': properties,
        'unique_tenants': unique_tenants,
        'selected_property': property_filter,
        'selected_tenant': tenant_filter,
        'selected_month': month_filter,
    }
    
    return render(request, 'user/homeowner_payment_history.html', context)

# Add this to your user/views.py file

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .forms import UserProfileForm  # You'll need to create this form

@login_required
def settings_view(request):
    # Get or create user profile at the start
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Initialize forms
    if request.method == 'POST':
        # Handle profile update
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
            
            # Handle avatar removal
            if 'remove_avatar' in request.POST and hasattr(request.user, 'profile'):
                if request.user.profile.avatar:
                    # Delete the old avatar file
                    if default_storage.exists(request.user.profile.avatar.name):
                        default_storage.delete(request.user.profile.avatar.name)
                    request.user.profile.avatar = None
                    request.user.profile.save()
                    messages.success(request, "Avatar removed successfully.")
                    return redirect('settings')
            
            if profile_form.is_valid():
                # Handle avatar upload
                if 'avatar' in request.FILES:
                    # Delete old avatar if exists
                    if request.user.profile.avatar:
                        if default_storage.exists(request.user.profile.avatar.name):
                            default_storage.delete(request.user.profile.avatar.name)
                    
                    # Save new avatar
                    request.user.profile.avatar = request.FILES['avatar']
                    request.user.profile.save()
                
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('settings')
            else:
                # Create fresh forms for other tabs
                password_form = PasswordChangeForm(request.user)
        
        # Handle password change
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # Update session to prevent logout
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully!")
                return redirect('settings')
            else:
                # Show password form errors
                profile_form = UserProfileForm(instance=request.user)
        
        # Handle notification settings update
        elif 'update_notifications' in request.POST:
            # Update email notifications
            profile.email_payment_reminders = 'email_payment_reminders' in request.POST
            profile.email_rental_expiry = 'email_rental_expiry' in request.POST
            profile.email_maintenance_updates = 'email_maintenance_updates' in request.POST
            profile.email_promotions = 'email_promotions' in request.POST
            
            # Update system notifications
            profile.system_payment_reminders = 'system_payment_reminders' in request.POST
            profile.system_rental_expiry = 'system_rental_expiry' in request.POST
            profile.system_maintenance_updates = 'system_maintenance_updates' in request.POST
            profile.system_promotions = 'system_promotions' in request.POST
            
            profile.save()
            messages.success(request, "Notification settings updated successfully!")
            return redirect('settings')
        
        # Handle account deletion
        elif 'delete_account' in request.POST:
            user = request.user
            # Clean up user data
            if hasattr(user, 'profile') and user.profile.avatar:
                if default_storage.exists(user.profile.avatar.name):
                    default_storage.delete(user.profile.avatar.name)
            
            # Delete the user
            user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect('landing_page')
    
    else:
        profile_form = UserProfileForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'profile': profile,
    }
    
    return render(request, 'user/settings.html', context)

@login_required
def delete_lease(request, rental_id):
    if request.user.user_type != 'home owner':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('dashboard')

    rental = get_object_or_404(Rental, id=rental_id, property__homeowner=request.user)
    
    if request.method == 'POST':
        rental.delete()
        messages.success(request, "Rental lease has been permanently deleted.")
    
    return redirect('booking_list')

@login_required
def delete_rental_request(request, request_id):
    if request.user.user_type != 'home owner':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('dashboard')

    rental_request = get_object_or_404(RentalRequest, id=request_id, property__homeowner=request.user)
    
    if request.method == 'POST':
        rental_request.delete()
        messages.success(request, "Rental request has been permanently deleted.")
    
    return redirect('booking_list')

