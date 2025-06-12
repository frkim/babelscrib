@echo off
REM Docker build and push script for BabelScrib development
REM Builds and pushes babelscrib:latest to Azure Container Registry

echo Building and pushing BabelScrib development image...
echo.

REM Set variables
set REGISTRY=babelscrib.azurecr.io
set IMAGE_NAME=babelscrib
set DEV_TAG=latest

echo 🔨 Building development image: %IMAGE_NAME%:%DEV_TAG%
docker build -t %IMAGE_NAME%:%DEV_TAG% .

if %errorlevel% neq 0 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo ✅ Build completed successfully!
echo.

echo 🏷️  Tagging image for registry: %REGISTRY%/%IMAGE_NAME%:%DEV_TAG%
docker tag %IMAGE_NAME%:%DEV_TAG% %REGISTRY%/%IMAGE_NAME%:%DEV_TAG%

if %errorlevel% neq 0 (
    echo ❌ Tagging failed!
    pause
    exit /b 1
)

echo ✅ Tagging completed successfully!
echo.

echo 🔐 Logging into Azure Container Registry...
echo Please enter your registry credentials when prompted.
docker login %REGISTRY%

if %errorlevel% neq 0 (
    echo ❌ Login failed!
    pause
    exit /b 1
)

echo ✅ Login successful!
echo.

echo 📤 Pushing image to registry...
docker push %REGISTRY%/%IMAGE_NAME%:%DEV_TAG%

if %errorlevel% neq 0 (
    echo ❌ Push failed!
    pause
    exit /b 1
)

echo ✅ Development image successfully pushed to registry!
echo.
echo 📋 Image details:
echo    Registry: %REGISTRY%
echo    Image: %IMAGE_NAME%:%DEV_TAG%
echo    Full path: %REGISTRY%/%IMAGE_NAME%:%DEV_TAG%
echo.

pause
