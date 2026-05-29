from django.contrib import admin
from .models import VendorProfile, PaymentMethod, PayoutMethod, Transaction, Payout

# Register your models here.
@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'available_balance', 'pending_balance', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', "updated_at")

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'is_default','created_at')
    list_filter = ('method_type', 'is_default')
    search_fields = ('user__username', 'gateway_token')
    readonly_fields = ('created_at', "updated_at")

@admin.register(PayoutMethod)
class PayouttMethodAdmin(admin.ModelAdmin):
    list_display = ('vendor_profile', 'method_type', 'is_default','is_active','created_at')
    list_filter = ('method_type', 'is_active')
    search_fields = ('vendor_profile__user__username', 'gateway_token')
    readonly_fields = ('created_at', "updated_at")

@admin.register(Transaction)
class TransationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'vendor_profile', 'amount', 'currency', 'status', 'created_at', 'held_until_at')
    list_filter = ('status', 'currency', 'transaction_type')
    search_fields = ('user__username', 'vendor_profile__user__username', 'gateway_reference', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor_profile', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('vendor_profile__user__username', 'gateway_reference', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')
