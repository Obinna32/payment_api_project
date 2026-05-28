from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

# Create your models here.
class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)], help_text="Funds immediately available for payout.")
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00), help_text="Funds held in escrow, awaiting customer confirmation or timeout"])
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