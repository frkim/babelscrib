#!/bin/bash
# Docker build and push script for BabelScrib production
# Builds and pushes babelscrib:prod to Azure Container Registry

echo "Building and pushing BabelScrib production image..."
echo ""

# Set variables
REGISTRY="babelscrib.azurecr.io"
IMAGE_NAME="babelscrib"
PROD_TAG="prod"

echo "🔨 Building production image: ${IMAGE_NAME}:${PROD_TAG}"
docker build -t ${IMAGE_NAME}:${PROD_TAG} -f Dockerfile.prod .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ Build completed successfully!"
echo ""

echo "🏷️  Tagging image for registry: ${REGISTRY}/${IMAGE_NAME}:${PROD_TAG}"
docker tag ${IMAGE_NAME}:${PROD_TAG} ${REGISTRY}/${IMAGE_NAME}:${PROD_TAG}

if [ $? -ne 0 ]; then
    echo "❌ Tagging failed!"
    exit 1
fi

echo "✅ Tagging completed successfully!"
echo ""

echo "🔐 Logging into Azure Container Registry..."
echo "Please enter your registry credentials when prompted."
docker login ${REGISTRY}

if [ $? -ne 0 ]; then
    echo "❌ Login failed!"
    exit 1
fi

echo "✅ Login successful!"
echo ""

echo "📤 Pushing image to registry..."
docker push ${REGISTRY}/${IMAGE_NAME}:${PROD_TAG}

if [ $? -ne 0 ]; then
    echo "❌ Push failed!"
    exit 1
fi

echo "✅ Production image successfully pushed to registry!"
echo ""
echo "📋 Image details:"
echo "   Registry: ${REGISTRY}"
echo "   Image: ${IMAGE_NAME}:${PROD_TAG}"
echo "   Full path: ${REGISTRY}/${IMAGE_NAME}:${PROD_TAG}"
echo ""
echo "⚠️  IMPORTANT: This is a PRODUCTION image!"
echo "   Ensure all environment variables are properly configured for production."
echo ""
