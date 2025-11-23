from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.throttling import AnonRateThrottle
from core.throttling import AuthRateThrottle


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [AuthRateThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthRateThrottle]

