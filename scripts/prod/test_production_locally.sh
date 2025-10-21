#!/bin/bash
# Test production-ready setup locally before deployment
# This script helps you verify authentication and all features work

echo "========================================"
echo "Investment Manager - Local Production Test"
echo "========================================"
echo ""

# Set environment variables for local testing
export FLASK_ENV=development
export SECRET_KEY=local-dev-secret-key-for-testing
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin123
export DATABASE_URL=sqlite:///investment_manager.db

echo "[INFO] Environment variables set for local testing:"
echo "  - FLASK_ENV: $FLASK_ENV"
echo "  - ADMIN_USERNAME: $ADMIN_USERNAME"
echo "  - ADMIN_PASSWORD: $ADMIN_PASSWORD"
echo ""

echo "[INFO] Starting backend server..."
echo ""
echo "========================================"
echo "  LOGIN CREDENTIALS:"
echo "  Username: admin"
echo "  Password: admin123"
echo "========================================"
echo ""
echo "Backend will start at: http://localhost:5000"
echo "Frontend should run at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python app.py

