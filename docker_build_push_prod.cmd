@echo off
REM Docker build and push script for BabelScrib production
REM Builds and pushes babelscrib:prod to Azure Container Registry

echo Building and pushing BabelScrib production image...
echo.

REM Set variables
set REGISTRY=babelscrib.azurecr.io
set IMAGE_NAME=babelscrib
set PROD_TAG=prod

echo 🔨 Building production image: %IMAGE_NAME%:%PROD_TAG%
docker build -t %IMAGE_NAME%:%PROD_TAG% -f Dockerfile.prod .

if %errorlevel% neq 0 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo ✅ Build completed successfully!
echo.

echo 🏷️  Tagging image for registry: %REGISTRY%/%IMAGE_NAME%:%PROD_TAG%
docker tag %IMAGE_NAME%:%PROD_TAG% %REGISTRY%/%IMAGE_NAME%:%PROD_TAG%

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
docker push %REGISTRY%/%IMAGE_NAME%:%PROD_TAG%

if %errorlevel% neq 0 (
    echo ❌ Push failed!
    pause
    exit /b 1
)

echo ✅ Production image successfully pushed to registry!
echo.
echo 📋 Image details:
echo    Registry: %REGISTRY%
echo    Image: %IMAGE_NAME%:%PROD_TAG%
echo    Full path: %REGISTRY%/%IMAGE_NAME%:%PROD_TAG%
echo.
echo ⚠️  IMPORTANT: This is a PRODUCTION image!
echo    Ensure all environment variables are properly configured for production.
echo.

pause
