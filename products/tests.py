from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Product, PrintableArea


class ProductModelTest(TestCase):
    """Test the Product model."""

    def setUp(self):
        self.product = Product.objects.create(
            name='T-Shirt',
            description='A cotton t-shirt',
            base_price=2500.00,
            category='apparel'
        )

    def test_create_product(self):
        """Test creating a product is successful."""
        self.assertEqual(self.product.name, 'T-Shirt')
        self.assertEqual(float(self.product.base_price), 2500.00)

    def test_create_printable_area(self):
        """Test creating a printable area for a product."""
        area = PrintableArea.objects.create(
            product=self.product,
            name='Front',
            x_position=100,
            y_position=100,
            width=300,
            height=400
        )
        self.assertEqual(area.product, self.product)
        self.assertEqual(area.name, 'Front')


class ProductAPITest(TestCase):
    """Test the product API."""

    def setUp(self):
        self.client = APIClient()
        Product.objects.create(
            name='T-Shirt',
            description='A cotton t-shirt',
            base_price=2500.00,
            category='apparel',
            is_active=True
        )

    def test_list_products(self):
        """Test listing products."""
        res = self.client.get('/api/products/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

    def test_get_product_detail(self):
        """Test getting product details."""
        product = Product.objects.first()
        res = self.client.get(f'/api/products/{product.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'T-Shirt')
