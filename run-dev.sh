#!/bin/bash

# Exit script immediately on error
set -e

# ---------------------------
# ⚙️ Run The Django Project
# ---------------------------

echo "🔄 Activating virtual environment..."
source venv/bin/activate

echo "📁 Changing into 'django/' directory..."
cd django

echo ""
echo "🎬==========================================="
echo "🎬  Flixifi: Upload & Stream Your Video"
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