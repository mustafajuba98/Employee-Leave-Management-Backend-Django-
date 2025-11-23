from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import User

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='EMPLOYEE'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'EMPLOYEE')

    def test_is_hr_property(self):
        self.assertFalse(self.user.is_hr)
        self.user.role = 'HR'
        self.user.save()
        self.assertTrue(self.user.is_hr)

    def test_is_employee_property(self):
        self.assertTrue(self.user.is_employee)
        self.user.role = 'HR'
        self.user.save()
        self.assertFalse(self.user.is_employee)

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser (EMPLOYEE)')
