@echo off
REM Docker build and run script for BabelScrib development
REM Image: babelscrib:latest
REM Uses .env file for environment variables

echo Building Docker development image...
docker build -t babelscrib:latest .

if %errorlevel% neq 0 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

REM Stop and remove existing container if running
docker stop babelscrib 2>nul
docker rm babelscrib 2>nul

echo.
echo Starting BabelScrib development container...
docker run -it --rm ^
  --name babelscrib ^
  --env-file .env ^
  -p 8000:8000 ^
  -v "%cd%":/app/mounted ^
  babelscrib:latest

pause
