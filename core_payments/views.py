from rest_framework import viewsets, mixins, status
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
    
class