from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import mark_notification_read, mark_all_notifications_read


urlpatterns = [
    # Main pages
    path('', views.landing_page, name='landing_page'),
    path('service/', views.service_page, name='service_page'),
    path('about/', views.about_page, name='about_page'),
    
    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('login/verify-otp/', views.login_verify_otp_view, name='login_verify_otp'),
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('reset-password/<uidb64>/<token>/', views.password_reset_view, name='password_reset'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('home/', views.home_view, name='home'),
    
    # Property general browsing
    path('properties/', views.properties_list, name='properties_list'),
    path('properties/<int:pk>/', views.property_detail, name='property_detail'),
     path('view_properties/<int:pk>/', views.view_property_detail, name='view_property_detail'),

    
    # Homeowner property management
    path('my-properties/', views.property_list, name='property_list'),
    path('my-properties/add/', views.add_property, name='add_property'),
    path('my-properties/edit/<int:property_id>/', views.edit_property, name='edit_property'),
    path('my-properties/delete/<int:property_id>/', views.delete_property, name='delete_property'),

    path('property-image/delete/<int:image_id>/', views.delete_property_image, name='delete_property_image'),
    path('property-image/set-primary/<int:image_id>/', views.set_primary_image, name='set_primary_image'),

    # Other Dashboard Features
    path('bookings/', views.booking_list, name='booking_list'),
    path('notifications/', views.notifications, name='notifications'),
    path('settings/', views.settings_view, name='settings'),
    path('payments/', views.payment_details, name='payment_details'),
    path('transactions/', views.transactions, name='transactions'),
    path('reports/', views.report, name='report'),


    # Tenant-specific views
    path('tenant/dashboard/', views.dashboard_view, name='dashboard'),  # Shared dashboard
    path('tenant/properties/', views.tenant_property_list, name='tenant_property_list'),
    path('tenant/rent/<int:property_id>/', views.rent_property, name='rent_property'),
    path('tenant/my-rentals/', views.my_rentals, name='my_rentals'),
    path('tenant/rent-payments/', views.rent_payments, name='rent_payments'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('tenant/create-checkout-session/<int:rental_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('tenant/payment-success/', views.payment_success, name='payment_success'),
    path('tenant/payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('tenant/payment-history/', views.tenant_payment_history, name='tenant_payment_history'),
    path('rental/<int:rental_id>/maintenance-request/', views.submit_maintenance_request, name='submit_maintenance_request'),
    path('maintenance/requests/', views.view_maintenance_requests, name='view_maintenance_requests'),

    # Homeowner Maintenance Management
    path('owner/maintenance/', views.owner_maintenance_requests, name='owner_maintenance_requests'),
    path('owner/maintenance/<int:request_id>/', views.maintenance_request_detail, name='maintenance_request_detail'),
    path('owner/maintenance/<int:request_id>/update/', views.update_maintenance_request, name='update_maintenance_request'),
    path('owner/maintenance/<int:request_id>/status/', views.update_maintenance_status, name='update_maintenance_status'),

    # Rental Request Management
    path('tenant/rental-requests/', views.my_rental_requests, name='my_rental_requests'),
    path('tenant/my-rentals/', views.my_rentals, name='my_rentals'),
    path('owner/rental-requests/', views.manage_rental_requests, name='manage_rental_requests'),
    path('owner/rental-requests/<int:request_id>/', views.rental_request_action, name='rental_request_action'),
    path('owner/rental-requests/<int:request_id>/detail/', views.rental_request_detail, name='rental_request_detail'),

    # Add these new URL patterns:
# Rental Lease Management
    path('tenant/pending-leases/', views.tenant_pending_leases, name='tenant_pending_leases'),
    path('tenant/sign-lease/<int:lease_id>/', views.sign_rental_lease, name='sign_rental_lease'),
    path('lease/view/<int:lease_id>/', views.view_rental_lease, name='view_rental_lease'),
    path('tenant/signed-leases/', views.tenant_signed_leases, name='tenant_signed_leases'),
    path('owner/signed-leases/', views.homeowner_signed_leases, name='homeowner_signed_leases'),
    path('owner/pending-leases/', views.homeowner_pending_leases, name='homeowner_pending_leases'),
    path('owner/sign-lease/<int:lease_id>/', views.homeowner_sign_lease, name='homeowner_sign_lease'),

    path('terminate-lease/<int:rental_id>/', views.terminate_lease, name='terminate_lease'),

    path('notifications/mark-read/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),

    path('owner/payment-history/', views.homeowner_payment_history, name='homeowner_payment_history'),

    path('delete-lease/<int:rental_id>/', views.delete_lease, name='delete_lease'),

    path('delete-rental-request/<int:request_id>/', views.delete_rental_request, name='delete_rental_request'),

]




# Serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)