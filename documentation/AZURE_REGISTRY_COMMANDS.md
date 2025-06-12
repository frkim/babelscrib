# Azure Container Registry Build and Push Guide

## Registry Information
- **Registry URL**: `babelscrib.azurecr.io`
- **Username**: `babelscrib`
- **Password**: `k+2awHP1VmMTYG3tsMFcofPCtn7aBNiP1J3yIXdjq0+ACRCTA1EA`

## Docker Commands

### 1. Login to Azure Container Registry
```bash
docker login babelscrib.azurecr.io -u babelscrib -p "YOUR_REGISTRY_KEY"
```

### 2. Build Docker Images

#### Build Development Image
```bash
docker build -t babelscrib:latest -f Dockerfile .
```

#### Build Production Image
```bash
docker build -t babelscrib:prod -f Dockerfile.prod .
```

### 3. Push Images to Registry

#### Push Development Image
```bash
docker push babelscrib:lastest
```

#### Push Production Image
```bash
docker push babelscrib:prod
```

### 4. Complete Build and Push Sequence

```bash
# Login
docker login babelscrib.azurecr.io -u babelscrib -p "k+2awHP1VmMTYG3tsMFcofPCtn7aBNiP1J3yIXdjq0+ACRCTA1EA"

# Build and push production image (recommended)
docker build -t babelscrib:prod -f Dockerfile.prod .
docker build -t babelscrib:latest -f Dockerfile.prod .
docker push babelscrib:prod
docker push babelscrib:latest

# Build and push Azure-optimized image
docker build -t babelscrib:azure -f Dockerfile.azure .
docker push babelscrib:azure
```

## Verify Push
After pushing, verify your images are in the registry:

```bash
# List repositories
az acr repository list --name babelscrib

# List tags for a repository
az acr repository show-tags --name babelscrib --repository babelscrib
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Password Security**: Consider using:
   - Azure CLI: `az acr login --name babelscrib`
   - Service Principal with more restricted permissions
   - GitHub Actions secrets for CI/CD

2. **Credential Rotation**: Regularly rotate ACR admin passwords

3. **Access Control**: Use RBAC instead of admin credentials when possible

## Recommended Production Image

For production deployment, use the **production image** (`Dockerfile.prod`):
- Multi-stage build for smaller size
- Gunicorn WSGI server
- Optimized for performance
- Production-ready configuration

```bash
docker build -t babelscrib:prod -f Dockerfile.prod .
docker push babelscrib:prod
```

## Deployment Commands for Azure Services

### Azure Container Apps
```bash
az containerapp create \
  --name babelscrib-app \
  --resource-group myResourceGroup \
  --environment myContainerAppEnv \
  --image babelscrib:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server babelscrib.azurecr.io \
  --registry-username babelscrib \
  --registry-password "YOUR_REGISTRY_KEY"
```

