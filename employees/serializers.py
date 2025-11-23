from rest_framework import serializers
from .models import Employee
from accounts.models import User


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'email', 'company_id', 'joining_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        if Employee.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("An employee with this email already exists.")
        return value

    def validate_joining_date(self, value):
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError("Joining date cannot be in the future.")
        return value


class EmployeeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['name', 'email', 'company_id', 'joining_date']
    
    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required and cannot be empty.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value.strip()
    
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        if Employee.objects.filter(email=value).exists():
            raise serializers.ValidationError("An employee with this email already exists.")
        return value.lower().strip()
    
    def validate_company_id(self, value):
        if value is None:
            raise serializers.ValidationError("Company ID is required.")
        if value <= 0:
            raise serializers.ValidationError("Company ID must be a positive number.")
        return value
    
    def validate_joining_date(self, value):
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError("Joining date cannot be in the future.")
        return value


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['name', 'email', 'company_id', 'joining_date']
    
    def validate_name(self, value):
        if value is not None:
            if not value.strip():
                raise serializers.ValidationError("Name cannot be empty.")
            if len(value.strip()) < 2:
                raise serializers.ValidationError("Name must be at least 2 characters long.")
            return value.strip()
        return value
    
    def validate_email(self, value):
        if value is not None:
            if self.instance and Employee.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("An employee with this email already exists.")
            return value.lower().strip()
        return value
    
    def validate_company_id(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Company ID must be a positive number.")
        return value
    
    def validate_joining_date(self, value):
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError("Joining date cannot be in the future.")
        return value

