from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('HR', 'HR'),
        ('EMPLOYEE', 'Employee'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='EMPLOYEE',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_hr(self):
        return self.role == 'HR'

    @property
    def is_employee(self):
        return self.role == 'EMPLOYEE'
