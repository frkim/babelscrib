# Docker Build and Run Scripts

This directory contains standardized scripts for building and running BabelScrib in both development and production modes.

## Prerequisites

1. **Docker** must be installed and running
2. **Environment file** (`.env`) must exist in the project root with your Azure configuration

## Available Scripts

### Development Scripts
- `docker_build_run_dev.cmd` (Windows)
- `docker_build_run_dev.sh` (Linux/macOS)

**Features:**
- Builds image as `babelscrib:latest`
- Uses regular `Dockerfile`
- Mounts current directory to `/app/mounted` for live development
- Container name: `babelscrib`

### Production Scripts
- `docker_build_run_prod.cmd` (Windows)
- `docker_build_run_prod.sh` (Linux/macOS)

**Features:**
- Builds image as `babelscrib:prod`
- Uses `Dockerfile.prod` for optimized production build
- No volume mounts for better security
- Container name: `babelscrib-prod`

## Usage

### Windows
```cmd
# Development
docker_build_run_dev.cmd

# Production
docker_build_run_prod.cmd
```

### Linux/macOS
```bash
# Development
chmod +x docker_build_run_dev.sh
./docker_build_run_dev.sh

# Production
chmod +x docker_build_run_prod.sh
./docker_build_run_prod.sh
```

## Environment Variables

All scripts use the `.env` file for configuration. Make sure to configure:
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_TRANSLATION_KEY`
- `AZURE_TRANSLATION_ENDPOINT`
- `AZURE_TRANSLATION_REGION`
- Other required environment variables

## Application Access

After running any script successfully:
- **URL**: http://localhost:8000
- **Logs**: `docker logs [container-name]`
- **Stop**: `docker stop [container-name]`

## Container Names
- Development: `babelscrib`
- Production: `babelscrib-prod`
