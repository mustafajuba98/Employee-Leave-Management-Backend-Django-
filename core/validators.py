from django.core.exceptions import ValidationError
from datetime import date


def validate_end_date_after_start_date(start_date, end_date):
    if end_date <= start_date:
        raise ValidationError("End date must be after start date.")


def validate_dates_not_in_past(start_date, end_date):
    today = date.today()
    if start_date < today:
        raise ValidationError("Start date cannot be in the past.")
    if end_date < today:
        raise ValidationError("End date cannot be in the past.")


def validate_no_overlapping_approved_leaves(employee, start_date, end_date, exclude_pk=None):
    from leaves.models import LeaveRequest
    
    overlapping_leaves = LeaveRequest.objects.filter(
        employee=employee,
        status='approved'
    )
    
    if exclude_pk:
        overlapping_leaves = overlapping_leaves.exclude(pk=exclude_pk)
    
    overlapping_leaves = overlapping_leaves.filter(
        start_date__lte=end_date,
        end_date__gte=start_date
    )
    
    if overlapping_leaves.exists():
        raise ValidationError(
            'An approved leave request already exists for this date range.'
        )

