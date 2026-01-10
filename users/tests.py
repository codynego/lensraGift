from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    """Test the User model."""

    def test_create_user_with_email(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'testpass123'
        user = User.objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='testpass123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


class UserAPITest(TestCase):
    """Test the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        """Test registering a new user."""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        res = self.client.post('/api/users/register/', payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', res.data)
        user = User.objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))

    def test_login_user(self):
        """Test logging in a user."""
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        res = self.client.post('/api/users/login/', payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)
