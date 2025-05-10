from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Customizing the UserAdmin for the CustomUser model
class CustomUserAdmin(admin.ModelAdmin):
    model = CustomUser
    # Fields to display in the admin list view
    list_display = ('username', 'email', 'user_type', 'date_joined')
    # Fields to filter in the admin view
    list_filter = ('user_type', 'date_joined')
    # Fields to search for in the admin view
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

# Register the CustomUser model with the customized admin interface
admin.site.register(CustomUser, CustomUserAdmin)


from django.contrib import admin
from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'property_type', 'location', 'homeowner', 'price', 'is_available')
    list_filter = ('property_type', 'is_available')
    search_fields = ('title', 'location', 'description')
    ordering = ('title',)
    
    # Optional: Add a filter to only show home owners in the dropdown
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "homeowner":
            kwargs["queryset"] = db_field.related_model.objects.filter(user_type='home owner')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    


from django.contrib import admin
from .models import RentPayment, Rental, Property  # import all related models

@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    list_display = ('rental', 'amount_paid', 'is_paid', 'paid_on')
    list_filter = ('is_paid',)
    search_fields = ('rental__property__title', 'rental__tenant__username')

# Optional: Register Rental too
@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('property__title', 'tenant__username', 'tenant__email')
    ordering = ('-start_date',)



from django.contrib import admin
from .models import MaintenanceRequest

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('subject', 'rental', 'property_owner', 'tenant', 'status', 'priority', 'request_date', 'is_resolved')
    list_filter = ('status', 'priority', 'is_resolved', 'request_date')
    search_fields = ('subject', 'description', 'rental__property__title', 'rental__tenant__email')
    ordering = ('-request_date',)
    readonly_fields = ('request_date',)
    
    fieldsets = (
        ('Request Information', {
            'fields': ('subject', 'description', 'attachment', 'priority', 'status', 'is_resolved')
        }),
        ('Rental Information', {
            'fields': ('rental',)
        }),
        ('Resolution Information', {
            'fields': ('resolved_date', 'resolved_by', 'admin_notes')
        }),
    )
    
    def property_owner(self, obj):
        return obj.rental.property.homeowner.email
    property_owner.short_description = 'Property Owner'
    
    def tenant(self, obj):
        return obj.rental.tenant.email
    tenant.short_description = 'Tenant'

    def has_add_permission(self, request):
        # Typically, only tenants should create maintenance requests
        return False  # Prevent admin from adding via UI if needed
