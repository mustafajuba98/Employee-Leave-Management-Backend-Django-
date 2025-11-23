from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from leaves.models import LeaveRequest
from employees.models import Employee
from accounts.models import User


class LeaveRequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='EMPLOYEE'
        )
        self.employee = Employee.objects.create(
            user=self.user,
            name='Test Employee',
            email='employee@example.com',
            company_id=123
        )
        self.leave_request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type='annual',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            status='pending'
        )

    def test_leave_request_creation(self):
        self.assertEqual(self.leave_request.employee, self.employee)
        self.assertEqual(self.leave_request.leave_type, 'annual')
        self.assertEqual(self.leave_request.status, 'pending')

    def test_end_date_after_start_date_validation(self):
        leave_request = LeaveRequest(
            employee=self.employee,
            leave_type='sick',
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=1),
            status='pending'
        )
        with self.assertRaises(ValidationError):
            leave_request.full_clean()

    def test_dates_not_in_past_validation(self):
        leave_request = LeaveRequest(
            employee=self.employee,
            leave_type='casual',
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=1),
            status='pending'
        )
        with self.assertRaises(ValidationError):
            leave_request.full_clean()

    def test_no_overlapping_approved_leaves(self):
        approved_leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type='annual',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            status='approved'
        )
        
        overlapping_leave = LeaveRequest(
            employee=self.employee,
            leave_type='sick',
            start_date=date.today() + timedelta(days=12),
            end_date=date.today() + timedelta(days=18),
            status='approved'
        )
        
        with self.assertRaises(ValidationError):
            overlapping_leave.full_clean()

    def test_leave_request_str(self):
        expected = f"{self.employee.name} - annual ({self.leave_request.start_date} to {self.leave_request.end_date})"
        self.assertEqual(str(self.leave_request), expected)
