from django.db import models
from django.core.validators import EmailValidator
from datetime import date
from accounts.models import User


class Employee(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        db_index=True
    )
    company_id = models.IntegerField(db_index=True)
    joining_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company_id']),
            models.Index(fields=['name']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.joining_date and self.joining_date > date.today():
            raise ValidationError({'joining_date': 'Joining date cannot be in the future.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
