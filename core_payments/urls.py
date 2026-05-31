from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, VendorProfileViewSet, PaymentMethodViewSet, PayoutMethodViewSet, TransactionViewSet, PayoutViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r'vendor-profiles', VendorProfileViewSet)
router.register(r'payment-methods', PaymentMethodViewSet)
router.register(r'payout-methods', PayoutMethodViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'payouts', PayoutViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
