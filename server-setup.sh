# server-setup.sh
#!/bin/bash

set -e

# Check if running as root
if [[ "$EUID" -ne 0 ]]; then
  echo "❌ This script must be run as root. Please use: sudo ./server-setup.sh"
  exit 1
fi

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
# 🔐 Install & Setup Docker
# ---------------------------

echo "🔍 Checking if curl is installed..."
if ! command -v curl >/dev/null 2>&1; then
  echo "🚀 Installing curl..."
  apt-get update && apt-get install -y curl
else
  echo "✅ curl is already installed."
fi

echo "🔍 Checking Docker installation..."
if ! [ -x "$(command -v docker)" ]; then
  echo "🚀 Installing Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
fi

echo "🔍 Checking Docker Compose..."
if ! [ -x "$(command -v docker-compose)" ]; then
  echo "🚀 Installing Docker Compose..."
  apt install -y docker-compose || sudo apt install -y docker-compose
fi

echo "✅ Docker is installed"

echo "🔧 Setting up folders..."
mkdir -p deploy/postgres deploy/redis django/media django/static

echo "🔄 Spinning up Docker containers..."
docker compose up --build

echo ""
echo "✅ Deployment complete!"
echo "🌐 Visit your app at: http://localhost"
