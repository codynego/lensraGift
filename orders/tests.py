from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product
from .models import Order, OrderItem
from decimal import Decimal

User = get_user_model()


class OrderModelTest(TestCase):
    """Test the Order model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='T-Shirt',
            description='A cotton t-shirt',
            base_price=2500.00,
            category='apparel'
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

    def test_create_order(self):
        """Test creating an order is successful."""
        self.assertEqual(self.order.order_number, 'TEST123')
        self.assertEqual(float(self.order.total_amount), 5000.00)

    def test_create_order_item(self):
        """Test creating an order item."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=2500.00
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(float(item.subtotal), 5000.00)


class OrderAPITest(TestCase):
    """Test the order API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(
            name='T-Shirt',
            description='A cotton t-shirt',
            base_price=2500.00,
            category='apparel'
        )

    def test_create_order(self):
        """Test creating an order through API."""
        payload = {
            'shipping_address': '123 Test St',
            'shipping_city': 'Lagos',
            'shipping_state': 'Lagos',
            'shipping_country': 'Nigeria',
            'phone_number': '08012345678',
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 2
                }
            ]
        }
        res = self.client.post('/api/orders/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_number', res.data)
