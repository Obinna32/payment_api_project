from rest_framework import viewsets, mixins, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import timedelta

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