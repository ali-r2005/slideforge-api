#!/bin/bash
set -e

echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-liberation \
    fonts-dejavu \
    libfreetype6

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating required directories..."
mkdir -p public/thumbnails
mkdir -p generated
mkdir -p temp_images

echo "Build completed successfully!"
