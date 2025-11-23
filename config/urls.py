from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from employees.views import EmployeeViewSet
from leaves.views import LeaveRequestViewSet
from core.views import health_check
from core.jwt_views import ThrottledTokenObtainPairView, ThrottledTokenRefreshView

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'leaves', LeaveRequestViewSet, basename='leave')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/token/', ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', ThrottledTokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
]
