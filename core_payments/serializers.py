from rest_framework import serializers
from django.contrib.auth.models import User
from .models import VendorProfile, PaymentMethod, PayoutMethod, Transaction, Payout, TransactionStatus, PaymentMethodType, PayoutMethodType, PayoutStatus
from decimal import Decimal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('username', 'email')

class VendorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    available_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    pending_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = VendorProfile
        fields = ('id', 'user', 'available_balance', 'pending_balance', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at',)

class PaymentMethodSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    method_type = serializers.ChoiceField(choices=PaymentMethodType.choices, required=True)
    details = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = PaymentMethod
        fields = ('id', 'user', 'method_type', 'gateway_token', 'details', 'is_default', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at',)

    def create(self, validated_data):
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
class PayoutMethodSerializer(serializers.ModelSerializer):
    vendor_profile = serializers.PrimaryKeyRelatedField(read_only=True)
    method_type = serializers.ChoiceField(choices=PayoutMethodType.choices, required=True)
    details = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = PayoutMethod
        fields = ('id', 'vendor_profile', 'method_type', 'gateway_token', 'details', 'is_default', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at',)

    def create(self, validated_data):
        request_user = self.context['request'].user
        try:
            vendor_profile = VendorProfile.objects.get(user=request_user)
        except VendorProfile.DoesNotExist:
            raise serializers.ValidationError("Only vendors can add payout methods.")
        validated_data['vendor_profile'] = vendor_profile
        return super().create(validated_data)