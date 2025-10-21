#!/bin/bash
# Development startup script for Investment Manager (Unix/Mac)

echo "========================================"
echo "Investment Manager - Development Mode"
echo "========================================"
echo ""

cd backend

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Set development environment variables
echo "Setting development environment..."
export FLASK_ENV=development
export SECRET_KEY=dev-secret-key-for-testing
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin123

echo ""
echo "Starting Flask backend (development mode)..."
echo "Backend will run on http://127.0.0.1:5000"
echo ""
echo "To start frontend, open another terminal and run:"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "Login: admin / admin123"
echo ""

python app.py

