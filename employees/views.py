from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
import logging
import asyncio
from .models import Employee
from .serializers import (
    EmployeeSerializer,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer
)
from .config import EXTERNAL_EMPLOYEE_API_URL
from .services import EmployeeSyncService
from core.permissions import IsHRUser
from core.exceptions import NetworkError, InvalidURLError, TimeoutError, InvalidDataError
from core.throttling import EmployeeSyncRateThrottle

logger = logging.getLogger('employees')


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    permission_classes = [IsAuthenticated, IsHRUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company_id']
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'email', 'created_at']
    ordering = ['-created_at']
    
    @method_decorator(cache_page(60 * 5))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmployeeUpdateSerializer
        return EmployeeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        logger.info(f"Employee created: {serializer.data['id']}")
        
        return Response(
            {
                'error': False,
                'message': 'Employee created successfully.',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['post'], throttle_classes=[EmployeeSyncRateThrottle])
    def sync(self, request):
        external_api_url = request.data.get('api_url', EXTERNAL_EMPLOYEE_API_URL)
        
        if not external_api_url:
            return Response(
                {
                    'error': True,
                    'message': 'API URL is required.',
                    'details': {'api_url': 'This field is required.'},
                    'code': 'validation_error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employees_data = asyncio.run(EmployeeSyncService.fetch_employees(external_api_url))
            new_count, updated_count = EmployeeSyncService.sync_employees(employees_data)
            
            logger.info(f"Employee sync completed. New: {new_count}, Updated: {updated_count}")
            
            return Response(
                {
                    'error': False,
                    'message': 'Employees synced successfully.',
                    'data': {
                        'new_employees': new_count,
                        'updated_employees': updated_count,
                        'total_processed': len(employees_data) if employees_data else 0
                    }
                },
                status=status.HTTP_200_OK
            )
        
        except (NetworkError, InvalidURLError, TimeoutError, InvalidDataError) as e:
            raise
        except Exception as e:
            logger.error(f"Employee sync failed: {str(e)}", exc_info=True)
            raise
