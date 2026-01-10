#!/bin/bash

# Lensra Backend Setup Script

echo "Setting up Lensra Print-On-Demand Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please update .env file with your configuration!"
fi

# Run migrations
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser prompt
echo ""
echo "Setup complete!"
echo ""
echo "To create a superuser, run: python manage.py createsuperuser"
echo "To start the development server, run: python manage.py runserver"
echo ""
