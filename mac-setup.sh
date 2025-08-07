#!/bin/bash

# Exit script immediately on error
set -e

# ---------------------------
# 🔐 Create .env Configuration
# ---------------------------

echo "🛠️ Creating .env file in 'django/' directory..."
touch .env

echo "🔐 Generating secure Django SECRET_KEY..."
echo "SECRET_KEY='$(openssl rand -base64 64 | tr -d '\n')'" > .env

echo "⚙️ Setting DEBUG=True for development..."
echo "DEBUG=True" >> .env

echo "🏷️ Setting PROJECT_NAME=Django HLS Stream..."
echo "PROJECT_NAME=Django HLS Stream" >> .env

echo "✅ .env file configured at: .env"

# ---------------------------
# 🐍 Setup Python Environment
# ---------------------------

echo "📦 Creating Python virtual environment..."
python3 -m venv venv

echo "✅ Virtual environment created."

echo "🔄 Activating virtual environment..."
source venv/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip
echo "✅ Pip upgraded."

echo "📦 Installing project dependencies from requirements.txt..."
pip install -r requirements.txt
echo "✅ Dependencies installed."

# ---------------------------
# ⚙️ Django Project Setup
# ---------------------------

echo "📁 Changing into 'django/' directory..."
cd django

echo "📄 Making migrations (if any)..."
python manage.py makemigrations

echo "🗃️ Applying database migrations..."
python manage.py migrate
echo "✅ Migrations complete."

echo "👤 Creating Django superuser (interactive prompt)..."
python manage.py createsuperuser

echo ""
echo "🎬==========================================="
echo "🎬  Django-HLS-Streaming: Upload & Stream Your Video"
echo "🎬==========================================="
echo ""
echo "📤 STEP 1: Upload a video using the Django admin panel"
echo "👉 URL: http://127.0.0.1:8000/admin/"
echo ""
echo "⚙️  STEP 2: Encode the uploaded video into HLS format"
echo "👉 Run: python manage.py encode"
echo ""
echo "OR"
echo ""
echo "🛠️  OPTIONAL: Start the Celery worker to handle tasks in background"
echo "👉 Run: celery -A home worker --loglevel=info"
echo ""
echo "✅ Done! Your video will be available for streaming once encoding finishes."
echo ""

echo "🚀 Starting Django development server..."
python manage.py runserver
