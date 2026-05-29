from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

# Create your models here.

class TransactionStatus(models.TextChoices):
    PENDING ="PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"

    INITIATED_HELD = "INITIATED_HELD", "Initiated (Held)"
    CONFIRMED_BY_CUSTOMER = "CONFIRMED_BY_CUSTOMER", "Confirmed by Customer"
    RELEASED_TO_VENDOR = "RELEASED_TO_VENDOR", "Released to Vendor"
    REFUNDED_BY_CUSTOMER = "REFUNDED_BY_CUSTOMER", "Refunded by Customer"
    RELEASED_BY_TIMEOUT = "RELEASED_BY_TIMEOUT", "Released by Timeout"

    CHARGEBACK_INITIATED = "CHARGEBACK_INITIATED", "Chargeback Initiated"
    CHARGEBACK_RESOLVED = "CHARGEBACK_RESOLVED", "Chargeback Resolved"

class PayoutStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"

class PaymentMethodType(models.TextChoices):
    CARD = "CARD", "Credit/Debit Card"
    MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
    BANK_ACCOUNT = "BANK_ACCOUNT", "Bank Account"

class PayoutMethodType(models.TextChoices):
    BANK_ACCOUNT = "BANK_ACCOUNT", "Bank Account"
    MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), help_text="Funds immediately available for payout.")
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), help_text="Funds held in escrow, awaiting customer confirmation or timeout")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"Vendor Profile for {self.user.username}"

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=PaymentMethodType.choices, default=PaymentMethodType.CARD)
    gateway_token = models.CharField(max_length=255, unique=True, help_text="Tokenized representation from the payment gateway (e.g., Stripe PaymentMethod ID, Flutterwave card token). DO NOT STORE RAW CARD DATA.")
    details = models.JSONField(blank=True, null=True, help_text="Masked details like card brand, last 4 digits, expiry month/year for user recognition.")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'gateway_token')

    def __str__(self):
        return f"{self.user.username}'s {self.get_method_type_display()} ({self.details.get('last4', '****') if self.details else 'No Details'})"
