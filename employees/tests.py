from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from employees.models import Employee
from accounts.models import User


class EmployeeModelTest(TestCase):
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
            company_id=123,
            joining_date=date.today()
        )

    def test_employee_creation(self):
        self.assertEqual(self.employee.name, 'Test Employee')
        self.assertEqual(self.employee.email, 'employee@example.com')
        self.assertEqual(self.employee.company_id, 123)

    def test_employee_email_unique(self):
        with self.assertRaises(Exception):
            Employee.objects.create(
                name='Another Employee',
                email='employee@example.com',
                company_id=456
            )

    def test_employee_joining_date_validation(self):
        future_date = date.today() + timedelta(days=1)
        employee = Employee(
            name='Future Employee',
            email='future@example.com',
            company_id=789,
            joining_date=future_date
        )
        with self.assertRaises(ValidationError):
            employee.full_clean()

    def test_employee_str(self):
        self.assertEqual(str(self.employee), 'Test Employee (employee@example.com)')
