from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from employees.models import Employee
from leaves.models import LeaveRequest

User = get_user_model()


class LeaveRequestAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.hr_user = User.objects.create_user(
            username='hruser',
            email='hr@example.com',
            password='hrpass123',
            role='HR'
        )
        self.employee_user = User.objects.create_user(
            username='employee',
            email='emp@example.com',
            password='emppass123',
            role='EMPLOYEE'
        )
        self.employee = Employee.objects.create(
            user=self.employee_user,
            name='Test Employee',
            email='employee@example.com',
            company_id=123
        )

    def test_create_leave_request_authenticated(self):
        self.client.force_authenticate(user=self.employee_user)
        data = {
            'leave_type': 'annual',
            'start_date': str(date.today() + timedelta(days=1)),
            'end_date': str(date.today() + timedelta(days=5))
        }
        response = self.client.post('/api/leaves/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['error'])

    def test_create_leave_request_unauthenticated(self):
        data = {
            'leave_type': 'annual',
            'start_date': str(date.today() + timedelta(days=1)),
            'end_date': str(date.today() + timedelta(days=5))
        }
        response = self.client.post('/api/leaves/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_approve_leave_request_hr_only(self):
        leave_request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type='annual',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            status='pending'
        )
        
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.patch(
            f'/api/leaves/{leave_request.id}/',
            {'status': 'approved'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'approved')

    def test_approve_leave_request_non_hr_forbidden(self):
        leave_request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type='annual',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            status='pending'
        )
        
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f'/api/leaves/{leave_request.id}/',
            {'status': 'approved'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_leaves_with_filters(self):
        LeaveRequest.objects.create(
            employee=self.employee,
            leave_type='annual',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            status='pending'
        )
        
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/leaves/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class EmployeeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.hr_user = User.objects.create_user(
            username='hruser',
            email='hr@example.com',
            password='hrpass123',
            role='HR'
        )

    def test_create_employee_hr_only(self):
        self.client.force_authenticate(user=self.hr_user)
        data = {
            'name': 'New Employee',
            'email': 'new@example.com',
            'company_id': 456
        }
        response = self.client.post('/api/employees/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['error'])

    def test_sync_employees(self):
        self.client.force_authenticate(user=self.hr_user)
        data = {
            'api_url': 'https://jsonplaceholder.typicode.com/users'
        }
        response = self.client.post('/api/employees/sync/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['error'])

