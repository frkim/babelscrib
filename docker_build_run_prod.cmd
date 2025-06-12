@echo off
REM Docker build and run script for BabelScrib production
REM Image: babelscrib:prod
REM Uses .env file for environment variables

echo Building Docker production image...
docker build -f Dockerfile.prod -t babelscrib:prod .

if %errorlevel% neq 0 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

REM Stop and remove existing container if running
docker stop babelscrib-prod 2>nul
docker rm babelscrib-prod 2>nul

echo.
echo Starting BabelScrib production container...
docker run -it --rm ^
  --name babelscrib-prod ^
  --env-file .env ^
  -p 8000:8000 ^
  babelscrib:prod

pause
