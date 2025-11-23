from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from .models import LeaveRequest
from .serializers import (
    LeaveRequestSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestUpdateStatusSerializer
)
from core.permissions import IsHRUser, IsOwnerOrHR
from core.throttling import CreateLeaveRateThrottle
import logging

logger = logging.getLogger('django')


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('employee').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'leave_type']
    search_fields = ['employee__name', 'employee__email']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'status', 'leave_type']
    ordering = ['-created_at']
    
    def get_throttles(self):
        if self.action == 'create':
            return [CreateLeaveRateThrottle()]
        return super().get_throttles()
    
    @method_decorator(cache_page(60 * 2))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            if 'status' in self.request.data:
                return LeaveRequestUpdateStatusSerializer
            return LeaveRequestSerializer
        return LeaveRequestSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'approve', 'reject']:
            return [IsAuthenticated(), IsHRUser()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrHR()]

    def get_queryset(self):
        queryset = super().get_queryset()
        employee_id = self.request.query_params.get('employee_id')
        
        if employee_id:
            try:
                employee_id = int(employee_id)
                if employee_id <= 0:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({'employee_id': 'Employee ID must be a positive number.'})
                queryset = queryset.filter(employee_id=employee_id)
            except ValueError:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'employee_id': 'Employee ID must be a valid number.'})
        
        if not self.request.user.is_hr:
            if hasattr(self.request.user, 'employee_profile'):
                queryset = queryset.filter(employee=self.request.user.employee_profile)
            else:
                queryset = queryset.none()
        
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        leave_id = serializer.instance.id if serializer.instance else None
        logger.info(f"Leave request created: {leave_id}")
        
        response_serializer = LeaveRequestSerializer(serializer.instance)
        headers = self.get_success_headers(response_serializer.data)
        
        return Response(
            {
                'error': False,
                'message': 'Leave request created successfully.',
                'data': response_serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if 'status' in request.data:
            serializer = LeaveRequestUpdateStatusSerializer(instance, data=request.data, partial=partial)
        else:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_update(serializer)
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                if '__all__' in e.message_dict:
                    raise DRFValidationError({'non_field_errors': e.message_dict['__all__']})
                else:
                    raise DRFValidationError(e.message_dict)
            elif hasattr(e, 'messages'):
                raise DRFValidationError({'non_field_errors': list(e.messages)})
            else:
                raise DRFValidationError({'non_field_errors': [str(e)]})
        
        logger.info(f"Leave request updated: {instance.id} - Status: {serializer.data.get('status')}")
        
        return Response(
            {
                'error': False,
                'message': 'Leave request updated successfully.',
                'data': serializer.data
            }
        )

    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        instance = self.get_object()
        serializer = LeaveRequestUpdateStatusSerializer(instance, data={'status': 'approved'}, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            serializer.save()
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                if '__all__' in e.message_dict:
                    raise DRFValidationError({'non_field_errors': e.message_dict['__all__']})
                else:
                    raise DRFValidationError(e.message_dict)
            elif hasattr(e, 'messages'):
                raise DRFValidationError({'non_field_errors': list(e.messages)})
            else:
                raise DRFValidationError({'non_field_errors': [str(e)]})
        
        logger.info(f"Leave request approved: {instance.id}")
        
        return Response(
            {
                'error': False,
                'message': 'Leave request approved successfully.',
                'data': serializer.data
            }
        )

    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        instance = self.get_object()
        serializer = LeaveRequestUpdateStatusSerializer(instance, data={'status': 'rejected'}, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            serializer.save()
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                if '__all__' in e.message_dict:
                    raise DRFValidationError({'non_field_errors': e.message_dict['__all__']})
                else:
                    raise DRFValidationError(e.message_dict)
            elif hasattr(e, 'messages'):
                raise DRFValidationError({'non_field_errors': list(e.messages)})
            else:
                raise DRFValidationError({'non_field_errors': [str(e)]})
        
        logger.info(f"Leave request rejected: {instance.id}")
        
        return Response(
            {
                'error': False,
                'message': 'Leave request rejected successfully.',
                'data': serializer.data
            }
        )
