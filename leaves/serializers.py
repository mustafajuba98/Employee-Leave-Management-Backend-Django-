from rest_framework import serializers
from .models import LeaveRequest
from employees.models import Employee
from datetime import date
from django.utils import timezone
from django.core.exceptions import ValidationError


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'leave_type', 'start_date', 'end_date', 'status',
            'approval_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'approval_date', 'created_at', 'updated_at']

    def _validate_dates(self, start_date, end_date):
        if not start_date or not end_date:
            return
        
        if end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        
        if start_date < date.today():
            raise serializers.ValidationError({
                'start_date': 'Start date cannot be in the past.'
            })
        
        if end_date < date.today():
            raise serializers.ValidationError({
                'end_date': 'End date cannot be in the past.'
            })

    def _validate_overlapping_leaves(self, employee, start_date, end_date, exclude_pk=None):
        if not employee or not start_date or not end_date:
            return
        
        from core.validators import validate_no_overlapping_approved_leaves
        try:
            validate_no_overlapping_approved_leaves(employee, start_date, end_date, exclude_pk)
        except ValidationError as e:
            raise serializers.ValidationError({
                'non_field_errors': [str(e)]
            })

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        employee = data.get('employee') or (self.instance.employee if self.instance else None)
        
        self._validate_dates(start_date, end_date)
        
        if employee and start_date and end_date:
            exclude_pk = self.instance.pk if self.instance else None
            self._validate_overlapping_leaves(employee, start_date, end_date, exclude_pk)
        
        return data


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.only('id', 'email'),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date']
    
    def validate_leave_type(self, value):
        valid_choices = ['annual', 'sick', 'casual']
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Leave type must be one of: {', '.join(valid_choices)}."
            )
        return value
    
    def validate_start_date(self, value):
        if not value:
            raise serializers.ValidationError("Start date is required.")
        if value < date.today():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value
    
    def validate_end_date(self, value):
        if not value:
            raise serializers.ValidationError("End date is required.")
        if value < date.today():
            raise serializers.ValidationError("End date cannot be in the past.")
        return value

    def _resolve_employee(self, data, request):
        employee = data.get('employee')
        
        if not request:
            raise serializers.ValidationError({
                'employee': 'Employee is required.'
            })
        
        if employee:
            if not request.user.is_hr:
                if not hasattr(request.user, 'employee_profile'):
                    raise serializers.ValidationError({
                        'employee': 'Employee profile not found. Please create an employee profile first.'
                    })
                if employee != request.user.employee_profile:
                    raise serializers.ValidationError({
                        'employee': 'You can only create leave requests for yourself.'
                    })
            return employee
        
        if hasattr(request.user, 'employee_profile'):
            return request.user.employee_profile
        
        raise serializers.ValidationError({
            'employee': 'Employee profile not found. Please create an employee profile first.'
        })

    def _validate_dates(self, start_date, end_date):
        if end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        
        if start_date < date.today():
            raise serializers.ValidationError({
                'start_date': 'Start date cannot be in the past.'
            })
        
        if end_date < date.today():
            raise serializers.ValidationError({
                'end_date': 'End date cannot be in the past.'
            })

    def _validate_overlapping_leaves(self, employee, start_date, end_date):
        if not employee or not start_date or not end_date:
            return
        
        from core.validators import validate_no_overlapping_approved_leaves
        try:
            validate_no_overlapping_approved_leaves(employee, start_date, end_date)
        except ValidationError as e:
            raise serializers.ValidationError({
                'non_field_errors': [str(e)]
            })

    def validate(self, data):
        request = self.context.get('request')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        employee = self._resolve_employee(data, request)
        data['employee'] = employee
        
        self._validate_dates(start_date, end_date)
        self._validate_overlapping_leaves(employee, start_date, end_date)
        
        return data


class LeaveRequestUpdateStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['status']

    def validate_status(self, value):
        valid_choices = ['approved', 'rejected']
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(valid_choices)}."
            )
        
        if self.instance and self.instance.status != 'pending':
            raise serializers.ValidationError(
                f"Only pending leave requests can be updated. Current status is '{self.instance.status}'."
            )
        
        return value

    def update(self, instance, validated_data):
        if validated_data.get('status') == 'approved':
            instance.approval_date = timezone.now()
        instance.status = validated_data.get('status', instance.status)
        instance.save(skip_date_validation=True)
        return instance

