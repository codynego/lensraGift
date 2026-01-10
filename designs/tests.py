from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product
from .models import Design
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

User = get_user_model()


class DesignModelTest(TestCase):
    """Test the Design model."""

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

    def test_create_design(self):
        """Test creating a design is successful."""
        design = Design.objects.create(
            user=self.user,
            product=self.product,
            name='Test Design'
        )
        self.assertEqual(design.name, 'Test Design')
        self.assertEqual(design.user, self.user)
        self.assertEqual(design.product, self.product)


class DesignAPITest(TestCase):
    """Test the design API."""

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

    def test_list_designs_authenticated(self):
        """Test listing designs requires authentication."""
        res = self.client.get('/api/designs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
