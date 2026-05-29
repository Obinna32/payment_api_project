from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone

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
    
class PayoutMethod(models.Model):
    vendor_profile = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='payout_methods')
    method_type = models.CharField(max_length=20, choices=PayoutMethodType.choices, default=PaymentMethodType.BANK_ACCOUNT)
    gateway_token = models.CharField(max_length=255, unique=True, help_text="Tokenized representation from the payout gateway (e.g., Flutterwave bank account token).")
    details = models.JSONField(blank=True, null=True, help_text="Masked details like bank name, account number last 4 digits, or mobile money number for vendor recognition.")
    is_default = models.BooleanField(default=False)
    is_active= models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('vendor_profile' 'gateway_token')

    def __str__(self):
        return f"{self.vendor_profile.user.username}'s Payout: {self.get_method_type_display()} ({self.details.get('last4', '****') if self.details else 'No Details'})"

    
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', help_text="The customer who initiated the transaction.")
    vendor_profile = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="received_transactions", help_text="The vendor profile receiving funds for this transaction (if applicable).")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(max_length=30, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, help_text="The customer's payment method used for this transaction.")
    gateway_reference = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="The Unique ID provided by the external payment gateway for this transaction.")
    transaction_type = models.CharField(max_length=50, help_text="E.g., 'charge', 'escrow_charge', 'refund', 'payout_transfer_to_vendor' (though payouts will have their own model)")
    description = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, help_text="Additional JSON data for the transaction.")

    held_until_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when held funds automatically release to vendor if not confirmed by customer.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.id} for {self.amount} {self.currency} - Status: {self.status}"
    
class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor_profile = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    payout_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, help_text="The method used for this payout.")
    status = models.CharField(max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.REQUESTED)
    gateway_reference = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Reference ID from the external payout gateway.")
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payout {self.id} for {self.vendor_profile.user.username} - {self.amount} {self.currency} - Status: {self.status}"