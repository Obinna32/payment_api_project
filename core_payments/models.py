from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

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
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)], help_text="Funds immediately available for payout.")
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)], help_text="Funds held in escrow, awaiting customer confirmation or timeout")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"Vendor Profile for {self.user.username}"
    
    def update_balance(self, amount, is_pending=True):
        if is_pending:
            self.pending_balance += amount
            if self.pending_balance < 0:
                raise ValueError("Pending balance cannot go less than zero.")
        else:
            self.available_balance += amount
            if self.available_balance < 0:
                raise ValueError("Available balance cannot go below zero.")
        self.save()

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
