from django.db import models
from django.core.exceptions import ValidationError
from datetime import date
from employees.models import Employee
from core.validators import (
    validate_end_date_after_start_date,
    validate_dates_not_in_past,
    validate_no_overlapping_approved_leaves
)


class LeaveRequest(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('annual', 'Annual'),
        ('sick', 'Sick'),
        ('casual', 'Casual'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        db_index=True
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPE_CHOICES,
        db_index=True
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_requests'
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status']),
            models.Index(fields=['leave_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['employee', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type} ({self.start_date} to {self.end_date})"

    def clean(self):
        validate_end_date_after_start_date(self.start_date, self.end_date)
        
        if not getattr(self, '_skip_date_validation', False):
            validate_dates_not_in_past(self.start_date, self.end_date)
        
        if self.status == 'approved':
            validate_no_overlapping_approved_leaves(self.employee, self.start_date, self.end_date, exclude_pk=self.pk)

    def save(self, *args, **kwargs):
        skip_date_validation = kwargs.pop('skip_date_validation', False)
        if skip_date_validation:
            self._skip_date_validation = True
        self.full_clean()
        if skip_date_validation:
            delattr(self, '_skip_date_validation')
        super().save(*args, **kwargs)
