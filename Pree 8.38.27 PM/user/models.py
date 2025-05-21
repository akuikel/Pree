from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('tenant', 'Tenant'),
        ('home owner', 'Home Owner'),
    )

    email = models.EmailField(unique=True,null=True)  # Ensuring unique emails for authentication
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    USERNAME_FIELD = 'email'  # Login with email instead of username
    REQUIRED_FIELDS = ['username']  # Keep username as an optional field if necessary

    def __str__(self):
        return self.email  # Display email instead of username


from django.conf import settings

class Property(models.Model):
    PROPERTY_TYPES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('land', 'Land'),
    ]
    
    homeowner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='properties',
        null=True,
        blank=True
    )
    
    title = models.CharField(max_length=200, default="Unnamed Property")
    location = models.CharField(max_length=200, default="Unknown Location")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='house')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bedrooms = models.IntegerField(null=True, blank=True, default=1)
    bathrooms = models.IntegerField(null=True, blank=True, default=1)
    description = models.TextField(default="No description available.")
    image = models.ImageField(upload_to='properties/', default='default_property.jpg')
    featured = models.BooleanField(default=False)
    
    is_available = models.BooleanField(default=True)  # New: To show if property is rented

    def __str__(self):
        return self.title
    
    @property
    def get_primary_image(self):
        # First try to get primary image from PropertyImage model
        primary_image = self.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image
        # If no primary image, try to get the first image from PropertyImage
        first_image = self.images.first()
        if first_image:
            return first_image.image
        # If no PropertyImage exists, fall back to the old image field
        if self.image and self.image.name != 'default_property.jpg':
            return self.image
        return None


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
    
    def __str__(self):
        return f"Image for {self.property.title}"

class Rental(models.Model):
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'tenant'}
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.tenant.email} rents {self.property.title}"


class RentPayment(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='payments')
    month = models.DateField()  # store the first day of the rent month
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.rental.tenant.email} paid for {self.month.strftime('%B %Y')}"

from django.db import models


class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='maintenance_requests')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateTimeField(blank=True, null=True)

    # Optional: who resolved it
    resolved_by = models.CharField(max_length=255, blank=True, null=True)

    # Optional: notes by homeowner or admin
    admin_notes = models.TextField(blank=True, null=True)

    # Optional: file attachment for issue (e.g., image of damage)
    attachment = models.FileField(upload_to='maintenance_attachments/', blank=True, null=True)

    def __str__(self):
        return f"Request by {self.rental.tenant.email} on {self.request_date.strftime('%Y-%m-%d')}"

    def clean(self):
        # Validate that attachments are images
        if self.attachment:
            ext = self.attachment.name.split('.')[-1].lower()
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
            if ext not in valid_extensions:
                raise ValidationError("Only image files are allowed for attachments.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-request_date']
        verbose_name = 'Maintenance Request'
        verbose_name_plural = 'Maintenance Requests'


class RentalRequest(models.Model):
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'tenant'},
        related_name='rental_requests'
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rental_requests')
    requested_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    
    def __str__(self):
        return f"{self.tenant.email} requests {self.property.title} ({self.get_status_display()})"


# Keep your existing LeaseAgreement model as is
class LeaseAgreement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text_message = models.TextField(blank=True, null=True)
    file_message = models.FileField(upload_to='lease_agreements/', blank=True, null=True)
    verification_doc = models.FileField(upload_to='lease_agreements/', blank=True, null=True)

    def __str__(self):
        return f"Lease Agreement for {self.user}"

# Add this new model for the rental-specific lease agreements
class RentalLeaseAgreement(models.Model):
    rental_request = models.OneToOneField(
        RentalRequest, 
        on_delete=models.CASCADE, 
        related_name='rental_lease_agreement'
    )
    rental = models.OneToOneField(
        Rental, 
        on_delete=models.CASCADE, 
        related_name='rental_lease_agreement',
        null=True,
        blank=True
    )
    lease_text = models.TextField()
    
    # Signature fields
    tenant_signed = models.BooleanField(default=False)
    tenant_signature = models.TextField(blank=True, null=True)  # Digital signature
    tenant_signed_at = models.DateTimeField(null=True, blank=True)
    
    homeowner_signed = models.BooleanField(default=False)
    homeowner_signature = models.TextField(blank=True, null=True)
    homeowner_signed_at = models.DateTimeField(null=True, blank=True)
    
    # Document fields
    lease_document = models.FileField(upload_to='rental_lease_documents/', blank=True, null=True)

    tenant_id_front = models.ImageField(upload_to='tenant_ids/', blank=True, null=True)
    tenant_id_back = models.ImageField(upload_to='tenant_ids/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Rental Lease for {self.rental_request.property.title} - {self.rental_request.tenant.email}"
    
    @property
    def is_fully_signed(self):
        return self.tenant_signed and self.homeowner_signed
    
# Add this to your user/models.py file

from django.db import models
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Notification preferences
    email_payment_reminders = models.BooleanField(default=True)
    email_rental_expiry = models.BooleanField(default=True)
    email_maintenance_updates = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=False)
    
    system_payment_reminders = models.BooleanField(default=True)
    system_rental_expiry = models.BooleanField(default=True)
    system_maintenance_updates = models.BooleanField(default=True)
    system_promotions = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


# Create a signal to automatically create a profile when a user is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)