# Lensra API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

Most endpoints require authentication using Token Authentication. Include the token in the request header:

```
Authorization: Token <your-token-here>
```

## Users API

### Register User
**POST** `/users/register/`

Request:
```json
{
    "email": "user@example.com",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "08012345678"
}
```

Response (201):
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "08012345678",
        "date_joined": "2024-01-10T10:00:00Z"
    },
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Login User
**POST** `/users/login/`

Request:
```json
{
    "email": "user@example.com",
    "password": "securepassword"
}
```

Response (200):
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "08012345678",
        "date_joined": "2024-01-10T10:00:00Z"
    },
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Get/Update Profile
**GET/PUT** `/users/profile/`

Requires: Authentication

Response (200):
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "08012345678",
    "date_joined": "2024-01-10T10:00:00Z"
}
```

## Products API

### List Products
**GET** `/products/`

Query Parameters:
- `category` - Filter by category
- `search` - Search in name and description
- `ordering` - Order by base_price or created_at

Response (200):
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Cotton T-Shirt",
            "base_price": "2500.00",
            "category": "apparel",
            "image": "/media/products/tshirt.jpg",
            "is_active": true
        }
    ]
}
```

### Get Product Details
**GET** `/products/{id}/`

Response (200):
```json
{
    "id": 1,
    "name": "Cotton T-Shirt",
    "description": "High quality cotton t-shirt",
    "base_price": "2500.00",
    "category": "apparel",
    "image": "/media/products/tshirt.jpg",
    "is_active": true,
    "printable_areas": [
        {
            "id": 1,
            "name": "Front",
            "x_position": 100,
            "y_position": 100,
            "width": 300,
            "height": 400
        }
    ],
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-10T10:00:00Z"
}
```

## Designs API

### List User Designs
**GET** `/designs/`

Requires: Authentication

Response (200):
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "user_email": "user@example.com",
            "product": 1,
            "product_details": {
                "id": 1,
                "name": "Cotton T-Shirt",
                "base_price": "2500.00",
                "category": "apparel",
                "image": "/media/products/tshirt.jpg",
                "is_active": true
            },
            "name": "My Cool Design",
            "design_image": "/media/designs/design1.jpg",
            "preview_image": "/media/design_previews/preview_design1.jpg",
            "created_at": "2024-01-10T10:00:00Z",
            "updated_at": "2024-01-10T10:00:00Z"
        }
    ]
}
```

### Create Design
**POST** `/designs/`

Requires: Authentication

Request (multipart/form-data):
```
product: 1
name: "My Cool Design"
design_image: <file>
```

Response (201):
```json
{
    "id": 1,
    "user": 1,
    "user_email": "user@example.com",
    "product": 1,
    "name": "My Cool Design",
    "design_image": "/media/designs/design1.jpg",
    "preview_image": "/media/design_previews/preview_design1.jpg",
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-10T10:00:00Z"
}
```

### Get Design Details
**GET** `/designs/{id}/`

Requires: Authentication

### Delete Design
**DELETE** `/designs/{id}/`

Requires: Authentication

## Orders API

### List User Orders
**GET** `/orders/`

Requires: Authentication

Response (200):
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "user_email": "user@example.com",
            "order_number": "ORD-ABC123XYZ789",
            "status": "pending",
            "total_amount": "5000.00",
            "shipping_address": "123 Main St",
            "shipping_city": "Lagos",
            "shipping_state": "Lagos",
            "shipping_country": "Nigeria",
            "shipping_postal_code": "100001",
            "phone_number": "08012345678",
            "payment_reference": null,
            "is_paid": false,
            "paid_at": null,
            "items": [
                {
                    "id": 1,
                    "product": 1,
                    "product_details": {
                        "id": 1,
                        "name": "Cotton T-Shirt",
                        "base_price": "2500.00",
                        "category": "apparel",
                        "image": "/media/products/tshirt.jpg",
                        "is_active": true
                    },
                    "design": 1,
                    "quantity": 2,
                    "unit_price": "2500.00",
                    "subtotal": "5000.00"
                }
            ],
            "created_at": "2024-01-10T10:00:00Z",
            "updated_at": "2024-01-10T10:00:00Z"
        }
    ]
}
```

### Create Order
**POST** `/orders/`

Requires: Authentication

Request:
```json
{
    "shipping_address": "123 Main St",
    "shipping_city": "Lagos",
    "shipping_state": "Lagos",
    "shipping_country": "Nigeria",
    "shipping_postal_code": "100001",
    "phone_number": "08012345678",
    "items": [
        {
            "product": 1,
            "design": 1,
            "quantity": 2
        }
    ]
}
```

Response (201):
```json
{
    "id": 1,
    "user": 1,
    "user_email": "user@example.com",
    "order_number": "ORD-ABC123XYZ789",
    "status": "pending",
    "total_amount": "5000.00",
    "shipping_address": "123 Main St",
    "shipping_city": "Lagos",
    "shipping_state": "Lagos",
    "shipping_country": "Nigeria",
    "shipping_postal_code": "100001",
    "phone_number": "08012345678",
    "payment_reference": null,
    "is_paid": false,
    "paid_at": null,
    "items": [...],
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-10T10:00:00Z"
}
```

### Get Order Details
**GET** `/orders/{id}/`

Requires: Authentication

## Payments API

### List User Payments
**GET** `/payments/`

Requires: Authentication

Response (200):
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "order": 1,
            "user": 1,
            "reference": "1234567890",
            "amount": "5000.00",
            "status": "success",
            "payment_method": "paystack",
            "access_code": "abc123xyz",
            "authorization_url": "https://checkout.paystack.com/abc123xyz",
            "created_at": "2024-01-10T10:00:00Z",
            "updated_at": "2024-01-10T10:05:00Z"
        }
    ]
}
```

### Initialize Payment
**POST** `/payments/initialize/`

Requires: Authentication

Request:
```json
{
    "order_id": 1,
    "email": "user@example.com"
}
```

Response (201):
```json
{
    "id": 1,
    "order": 1,
    "user": 1,
    "reference": "1234567890",
    "amount": "5000.00",
    "status": "pending",
    "payment_method": "paystack",
    "access_code": "abc123xyz",
    "authorization_url": "https://checkout.paystack.com/abc123xyz",
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-10T10:00:00Z"
}
```

### Verify Payment
**POST** `/payments/verify/`

Requires: Authentication

Request:
```json
{
    "reference": "1234567890"
}
```

Response (200):
```json
{
    "message": "Payment verified successfully",
    "payment": {
        "id": 1,
        "order": 1,
        "user": 1,
        "reference": "1234567890",
        "amount": "5000.00",
        "status": "success",
        "payment_method": "paystack",
        "access_code": "abc123xyz",
        "authorization_url": "https://checkout.paystack.com/abc123xyz",
        "created_at": "2024-01-10T10:00:00Z",
        "updated_at": "2024-01-10T10:05:00Z"
    }
}
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "Error message describing what went wrong"
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error message"
}
```
