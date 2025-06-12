#!/bin/bash
# Docker build and run script for BabelScrib development
# Image: babelscrib:latest
# Uses .env file for environment variables

echo "Building Docker development image..."
docker build -t babelscrib:latest .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Stop and remove existing container if running
docker stop babelscrib 2>/dev/null
docker rm babelscrib 2>/dev/null

echo ""
echo "Starting BabelScrib development container..."
docker run -it --rm \
  --name babelscrib \
  --env-file .env \
  -p 8000:8000 \
  -v "$(pwd)":/app/mounted \
  babelscrib:latest
