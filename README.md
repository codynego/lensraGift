# Lensra Print-On-Demand Backend

A Nigeria-first Print-On-Demand platform backend built with Django and Django Rest Framework.

## Features

- **Custom Email Authentication**: User registration and login using email instead of username
- **Products Management**: Base products with printable areas for customization
- **Design Uploads**: Users can upload custom designs with automatic preview generation
- **Order Management**: Complete order and order items workflow
- **Payment Integration**: Paystack payment gateway integration for Nigerian market
- **RESTful API**: Clean API endpoints with DRF serializers and generics

## Tech Stack

- **Django 4.2.26**: Web framework (latest security patch)
- **Django REST Framework 3.14.0**: API framework
- **PostgreSQL**: Database (via psycopg2-binary)
- **Pillow 10.3.0**: Image processing for design previews (security patched)
- **Paystack**: Payment gateway integration
- **django-cors-headers**: CORS support for frontend integration

## Project Structure

```
lensra/
├── users/          # Custom email-based authentication
├── products/       # Product catalog with printable areas
├── designs/        # User design uploads and previews
├── orders/         # Order and order items management
├── payments/       # Paystack payment integration
└── lensra/         # Project settings and configuration
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/codynego/lensraGift.git
cd lensraGift
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run development server:
```bash
python manage.py runserver
```

## API Endpoints

### Users
- `POST /api/users/register/` - Register new user
- `POST /api/users/login/` - Login user
- `GET /api/users/profile/` - Get user profile
- `PUT /api/users/profile/` - Update user profile

### Products
- `GET /api/products/` - List all products
- `GET /api/products/<id>/` - Get product details with printable areas

### Designs
- `GET /api/designs/` - List user designs
- `POST /api/designs/` - Upload new design
- `GET /api/designs/<id>/` - Get design details
- `DELETE /api/designs/<id>/` - Delete design

### Orders
- `GET /api/orders/` - List user orders
- `POST /api/orders/` - Create new order
- `GET /api/orders/<id>/` - Get order details

### Payments
- `POST /api/payments/initialize/` - Initialize payment with Paystack
- `POST /api/payments/verify/` - Verify payment status
- `GET /api/payments/` - List user payments

## Environment Variables

Create a `.env` file with the following variables:

```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_NAME=lensra_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_PUBLIC_KEY=your-paystack-public-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Testing

Run tests:
```bash
python manage.py test
```

Run tests for specific app:
```bash
python manage.py test users
python manage.py test products
python manage.py test designs
python manage.py test orders
python manage.py test payments
```

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to manage:
- Users
- Products and Printable Areas
- Designs
- Orders and Order Items
- Payments

## Models

### User
Custom user model with email authentication:
- email (unique)
- first_name, last_name
- phone_number
- is_active, is_staff
- date_joined

### Product
Base products for customization:
- name, description
- base_price, category
- image
- printable_areas (related)

### PrintableArea
Defines where designs can be placed:
- product (FK)
- name
- x_position, y_position
- width, height

### Design
User-uploaded designs:
- user (FK), product (FK)
- name
- design_image, preview_image (auto-generated)

### Order
Customer orders:
- user (FK)
- order_number (unique)
- status, total_amount
- shipping details
- payment_reference, is_paid

### OrderItem
Individual items in orders:
- order (FK), product (FK), design (FK optional)
- quantity, unit_price, subtotal

### Payment
Payment transactions:
- order (OneToOne), user (FK)
- reference (unique)
- amount, status
- Paystack integration fields

## License

MIT