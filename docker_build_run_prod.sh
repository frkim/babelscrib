#!/bin/bash
# Docker build and run script for BabelScrib production
# Image: babelscrib:prod
# Uses .env file for environment variables

echo "Building Docker production image..."
docker build -f Dockerfile.prod -t babelscrib:prod .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Stop and remove existing container if running
docker stop babelscrib-prod 2>/dev/null
docker rm babelscrib-prod 2>/dev/null

echo ""
echo "Starting BabelScrib production container..."
docker run -it --rm \
  --name babelscrib-prod \
  --env-file .env \
  -p 8000:8000 \
  babelscrib:prod
