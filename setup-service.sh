#!/bin/bash

# setup-service.sh

SERVICE_NAME="docker-compose-app"
SERVICE_FILE="${SERVICE_NAME}.service"
TARGET_DIR="/etc/systemd/system"
PROJECT_DIR=$(pwd)

# Check if running as root
if [[ "$EUID" -ne 0 ]]; then
  echo "❌ This script must be run as root. Please use:"
  echo "   sudo ./setup-service.sh"
  exit 1
fi

echo "📦 Setting up systemd service for Docker Compose..."

# Check if service file exists in current directory
if [ ! -f "$SERVICE_FILE" ]; then
  echo "❌ Service file '$SERVICE_FILE' not found in current directory."
  exit 1
fi

# Copy to systemd directory
echo "🔧 Copying $SERVICE_FILE to $TARGET_DIR..."
cp "$SERVICE_FILE" "$TARGET_DIR"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reexec
systemctl daemon-reload

# Enable service
echo "📌 Enabling $SERVICE_NAME..."
systemctl enable "$SERVICE_NAME"

# Start service
echo "🚀 Starting $SERVICE_NAME..."
systemctl start "$SERVICE_NAME"

# Show status
echo "📋 Checking status:"
systemctl status "$SERVICE_NAME" --no-pager

echo "✅ Service installed and started!"