from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import Order
from .models import Payment

User = get_user_model()


class PaymentModelTest(TestCase):
    """Test the Payment model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            total_amount=5000.00,
            shipping_address='123 Test St',
            shipping_city='Lagos',
            shipping_state='Lagos',
            phone_number='08012345678'
        )

    def test_create_payment(self):
        """Test creating a payment is successful."""
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            reference='TEST_REF_123',
            amount=5000.00
        )
        self.assertEqual(payment.reference, 'TEST_REF_123')
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(float(payment.amount), 5000.00)


class PaymentAPITest(TestCase):
    """Test the payment API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_payments(self):
        """Test listing payments requires authentication."""
        res = self.client.get('/api/payments/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
