# Infrastructure Updates - Azure Bicep Template

## Overview

The `main.bicep` file has been completely updated to follow Azure best practices for security, reliability, and maintainability. This document outlines the key improvements and changes made.

## Key Improvements

### 1. Security Enhancements

#### Managed Identity Implementation
- **User-Assigned Managed Identity**: Created a centralized managed identity for secure resource access
- **Role-Based Access Control (RBAC)**: Proper role assignments for:
  - ACR Pull access for container images
  - Storage Blob Data Contributor for document storage
  - Cognitive Services User for translation services
- **Secret Management**: Parameterized sensitive values like client secrets
- **No Hardcoded Credentials**: All authentication uses managed identities

#### Resource Security
- **Storage Account**: 
  - Disabled shared key access
  - Enabled OAuth authentication by default
  - Disabled public blob access
  - Enforced HTTPS traffic only
- **Container Registry**: 
  - Disabled admin user
  - Secure authentication via managed identity
- **Container Apps**: 
  - CORS policy configuration
  - Proper health checks and probes

### 2. Resource Naming and Organization

#### Consistent Naming Convention
- Uses `resourceToken` (unique string) for global uniqueness
- Standardized naming patterns:
  - `cr{token}` for Container Registry
  - `st{token}` for Storage Account
  - `log-{token}` for Log Analytics
  - `ca-babelscrib-{env}-{token}` for Container Apps

#### Environment Support
- Conditional deployment based on `environmentName` parameter
- Separate configurations for production and development
- Environment-specific scaling and resource allocation

### 3. Configuration Improvements

#### Parameterization
- Comprehensive parameter validation with descriptions
- Secure parameters for sensitive data
- Environment-specific defaults
- Resource allocation parameters for different environments

#### Template Structure
- Target scope definition
- Comprehensive variable definitions
- Proper resource dependencies
- Detailed outputs for downstream consumption

### 4. Container App Enhancements

#### Production Container App
- Proper health checks with realistic timeouts
- Auto-scaling based on HTTP requests
- Custom domain support (conditional for production)
- Comprehensive environment variables for Azure service integration
- Managed identity authentication

#### Development Container App
- Conditional deployment (only for non-prod environments)
- Reduced resource allocation
- Debug mode configuration
- Separate scaling rules

### 5. Monitoring and Observability

#### Log Analytics
- Daily quota limits to control costs
- Configurable retention periods
- Proper workspace capping

#### Health Checks
- Liveness probes with `/health/` endpoint
- Readiness probes with `/ready/` endpoint
- Configurable timeouts and failure thresholds

## Deployment Requirements

### Prerequisites
1. Azure subscription with appropriate permissions
2. Resource group created
3. Azure CLI or Azure PowerShell installed
4. Bicep CLI installed

### Required Parameters
- `microsoftClientId`: OAuth client ID
- `microsoftClientSecret`: OAuth client secret (use Key Vault reference)

### Optional Parameters
- `environmentName`: 'dev', 'staging', or 'prod' (default: 'prod')
- `location`: Azure region (default: 'westeurope')
- `domainName`: Custom domain name (default: 'babelscrib.com')

## Deployment Commands

### Using Azure CLI
```bash
# Deploy to resource group
az deployment group create \
  --resource-group myResourceGroup \
  --template-file infrastructure/main.bicep \
  --parameters infrastructure/main.parameters.json

# What-if deployment (preview changes)
az deployment group what-if \
  --resource-group myResourceGroup \
  --template-file infrastructure/main.bicep \
  --parameters infrastructure/main.parameters.json
```

### Using Azure Developer CLI (AZD)
```bash
# Initialize and deploy
azd init
azd up
```

## Breaking Changes from Previous Version

1. **Resource Names**: All resource names now use token-based naming
2. **Authentication**: Switched from system-assigned to user-assigned managed identity
3. **Parameters**: Added required secure parameters for OAuth configuration
4. **Container Registry**: Authentication method changed to managed identity
5. **Environment Variables**: Expanded container app environment variables

## Post-Deployment Configuration

1. **DNS Configuration**: Update DNS records to point to container app FQDN
2. **Certificate**: Verify managed certificate is properly issued
3. **OAuth App**: Update OAuth app redirect URIs to match new FQDNs
4. **Application Settings**: Verify application can authenticate with Azure services

## Outputs

The template provides comprehensive outputs including:
- Resource identifiers and endpoints
- Container app FQDNs
- Managed identity details
- Service endpoints for application configuration

## Cost Optimization

- Log Analytics workspace with daily quota limits
- Container Apps with appropriate scaling limits
- Standard tier services where Premium features aren't required
- Development resources only deployed in non-production environments

## Security Considerations

- All secrets should be stored in Azure Key Vault
- Managed identities eliminate credential management
- RBAC follows principle of least privilege
- Network security can be enhanced with private endpoints (future enhancement)

## Next Steps

1. Review and update the `main.parameters.json` file with your specific values
2. Configure Key Vault for secret management
3. Set up CI/CD pipeline for automated deployments
4. Consider implementing private endpoints for enhanced security
5. Set up monitoring and alerting for the deployed resources
