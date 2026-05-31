from rest_framework import viewsets, mixins, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction, models
from django.utils import timezone
from datetime import timedelta

import uuid

from .models import VendorProfile, PaymentMethod, PayoutMethod, Transaction, Payout, TransactionStatus, PaymentMethodType, PayoutMethodType, PayoutStatus

from .serializers import UserSerializer, VendorProfileSerializer, PaymentMethodSerializer, PayoutMethodSerializer, TransactionSerializer, PayoutSerializer

# Create your views here.
class IsVendor(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and hasattr(request.user, 'vendor_profile')
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'vendor_profile'):
            return obj.vendor_profile.user == request.user
        elif hasattr(obj, 'user') and hasattr(obj.user, 'vendor_profile'):
            return obj.user.vendor_profile.user == request.user
        return False
    
class IsOwner(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class VendorProfileViewSet(viewsets.ModelViewSet):
    queryset = VendorProfile.objects.all()
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'vendor_profile'):
            return self.queryset.filter(user=self.request.user)
        return self.queryset.none()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        if hasattr(self.request.user, 'vendor_profile'):
            raise serializers.ValidationError("User already has a vendor profile.")
        serializer.save(user=self.request.user)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(User=self.request.user)

class PayoutMethodViewSet(viewsets.ModelViewSet):
    queryset = PayoutMethod.objects.all()
    serializer_class = PayoutMethodSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    def get_queryset(self):
        if hasattr(self.request.user, 'vendor_profile'):
            return self.queryset.filter(vendor_profile=self.request.user.vendor_profile)
        return self.queryset.none()
    
    def perform_create(self, serializer):
        serializer.save(vendor_profile = self.request.user.vendor_profile)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, 'vendor_profile'):
            return self.queryset.filter(
                models.Q(user=self.request.user) | models.Q(vendor_profile__user=self.request.user)
            )
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        with db_transaction.atomic():
            payment_method_id = serializer.validated_data.get('payment_method')
            if not payment_method_id:
                raise serializers.ValidationError({"payment_method": "Payment method is required."})
            payment_method = get_object_or_404(
                PaymentMethod, id=payment_method_id.id, user=self.request.user
            )
            mock_gateway_reference = f"mock_ref_{uuid.uui4().hex}"
            gateway_success = True

            if not gateway_success:
                serializer.validated_data['status'] = TransactionStatus.FAILED
                transaction = serializer.save(
                    user=self.request.user,
                    gateway_reference = mock_gateway_reference
                )
                return
            
            transaction_type = serializer.validated_data.get('transaction_type')
            vendor_profile = serializer.validated_data.get('vendor_profile')
            amount = serializer.validated_data['amount']

            if transaction_type == 'escrow_charge' and vendor_profile:
                serializer.validated_data['status'] = TransactionStatus.INITIATED_HELD
                serializer.validated_data['held_until_at'] = timezone.now() + timedelta(hours=24)

                vendor_profile.pending_balance += amount
                vendor_profile.save()

            else:
                serializer.validated_data['status'] = TransactionStatus.SUCCESS
                if vendor_profile:
                    vendor_profile.available_balance += amount
                    vendor_profile.save()
            
            transaction = serializer.save(
                user = self.request.user,
                gateway_reference = mock_gateway_reference
            )
        
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwner])
    def confirm(self, request, pk=None):
        transaction_to_confim = get_object_or_404(Transaction.objects.select_related('vendor_profile', 'user'),
                                                  pk=pk, user=request.user, status=TransactionStatus.INITIATED_HELD)
        
        with db_transaction.atomic():
            transaction_to_confim.status = TransactionStatus.CONFIRMED_BY_CUSTOMER
            transaction_to_confim.save()

            vendor_profile = transaction_to_confim.vendor_profile
            amount = transaction_to_confim.amount

            if vendor_profile:
                vendor_profile.pending_balance -= amount
                vendor_profile.available_balance += amount
                vendor_profile.save()
            else:
                return Response(
                    {"detail": "No vendor associated with this escrow transaction."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        serializer = self.get_serializer(transaction_to_confim)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwner])
    def refund_self(self, request, pk=None):
        transaction_to_refund = get_object_or_404(
            Transaction.objects.select_related('vendor_profile', 'user', 'payment_method'),
            pk=pk, user=request.user, status=TransactionStatus.INITIATED_HELD
        )
        with db_transaction.atomic():
            transaction_to_refund.status = TransactionStatus.REFUNDED_BY_CUSTOMER
            transaction_to_refund.save()

            vendor_profile = transaction_to_refund.vendor_profile
            amount = transaction_to_refund.amount

            if vendor_profile:
                vendor_profile.pending_balance -= amount
                vendor_profile.save()

        serializer = self.get_serializer(transaction_to_refund)
        return Response(serializer.data, status=status.HTTP_200_OK)