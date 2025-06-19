# Microsoft Authentication Setup Guide

This guide provides a complete setup for Microsoft Entra ID (formerly Azure AD) authentication in your BabelScrib Django application running on Azure Container Apps.

## Problem Statement
If you encounter this error:
```
AADSTS50011: The redirect URI 'https://dev.babelscrib.com/.auth/login/aad/callback' specified in the request does not match the redirect URIs configured for the application.
```

## Root Cause
This error occurs when using Azure App Service's Easy Auth patterns with Azure Container Apps, which requires application-level authentication handling instead of platform-managed authentication.

## Solution: Django-based Authentication with Microsoft Entra ID

The BabelScrib application implements Microsoft authentication using `django-allauth` with the Microsoft provider. This approach provides:
- **Complete control** over the authentication flow
- **Seamless integration** with Django's user management system
- **Container Apps compatibility** without platform-specific dependencies
- **Enhanced security** with proper token management

### Current Implementation Status ✅

#### 1. Django Configuration (Completed)
- ✅ `django-allauth` and Microsoft provider added to `INSTALLED_APPS`
- ✅ Required middleware: `allauth.account.middleware.AccountMiddleware`
- ✅ Authentication backends configured for both Django and social authentication
- ✅ Site framework configured with SITE_ID = 1

#### 2. URL Configuration (Completed)
- ✅ Allauth URLs integrated: `path('accounts/', include('allauth.urls'))`
- ✅ Custom authentication templates in place

#### 3. Dependencies (Completed)
- ✅ `msal==1.24.0` - Microsoft Authentication Library for Python
- ✅ `django-allauth==0.57.0` - Social authentication for Django

#### 4. Database Setup (Completed)
- ✅ Social authentication tables migrated
- ✅ Setup scripts available: `setup_social_app.py` and `update_social_app.py`

## Microsoft Entra ID Configuration

### Prerequisites
- Access to Azure Portal with Application Administrator role
- Your application ID: `fcfbaf73-654e-49a7-9141-b994192888c6`

### Step 1: Configure App Registration
1. Navigate to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations**
2. Select your application: `fcfbaf73-654e-49a7-9141-b994192888c6`

#### Authentication Configuration
1. Go to **Authentication** tab
2. Add these **Web** platform redirect URIs:
   ```
   Production:  https://babelscrib.com/accounts/microsoft/login/callback/
   Development: https://dev.babelscrib.com/accounts/microsoft/login/callback/
   Local:       http://localhost:8000/accounts/microsoft/login/callback/
   ```
3. Under **Implicit grant and hybrid flows**:
   - ✅ Enable "ID tokens" for OpenID Connect authentication
4. Under **Advanced settings**:
   - ✅ Allow public client flows: No (keep disabled for security)
5. Click **Save**

#### API Permissions (Recommended)
1. Go to **API permissions** tab
2. Ensure these Microsoft Graph permissions are granted:
   - `openid` (OpenID Connect sign-in)
   - `profile` (View users' basic profile)
   - `email` (View users' email address)
   - `User.Read` (Sign in and read user profile)

### Step 2: Generate Client Secret
1. Go to **Certificates & secrets** tab
2. Click **+ New client secret**
3. Add description: "BabelScrib Production Secret"
4. Set expiration: **24 months** (recommended for production)
5. **IMPORTANT**: Copy the secret value immediately - it won't be shown again
6. Store securely in your password manager or Azure Key Vault

### Step 3: Note Application Details
Record these values for environment configuration:
```
Tenant ID: [Your tenant ID] (found in Overview tab)
Client ID: fcfbaf73-654e-49a7-9141-b994192888c6
Client Secret: [The value you just copied]
```

## Environment Configuration

### Required Environment Variables

#### For Local Development (.env file)
Create a `.env` file in your project root:
```env
# Microsoft Authentication
MICROSOFT_CLIENT_ID=fcfbaf73-654e-49a7-9141-b994192888c6
MICROSOFT_CLIENT_SECRET=your-actual-client-secret-here
MICROSOFT_TENANT_ID=your-tenant-id-here

# Django Configuration
SECRET_KEY=your-django-secret-key
DEBUG=True
DJANGO_LOG_ENV_VARS=True

# Azure Services (for translation features)
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
AZURE_TRANSLATION_KEY=your-translation-key
AZURE_TRANSLATION_ENDPOINT=your-translation-endpoint
```

#### For Azure Container Apps (Production)
These environment variables are configured in your Bicep infrastructure:
- `MICROSOFT_CLIENT_ID` - Set as environment variable
- `MICROSOFT_CLIENT_SECRET` - Set as secret reference
- `MICROSOFT_TENANT_ID` - Set as environment variable

### Updating Social App Configuration

After setting environment variables, run the setup script to configure django-allauth:

```bash
# For initial setup
python setup_social_app.py

# For updating existing configuration
python update_social_app.py
```

These scripts will:
- Create/update the Microsoft SocialApp in Django admin
- Configure provider-specific settings (tenant, scopes)
- Associate with the correct Django site

## Infrastructure Configuration

### Azure Container Apps Setup

Your `infrastructure/main.bicep` includes Microsoft authentication configuration:

#### Secrets Configuration
```bicep
secrets: [
  {
    name: 'microsoft-client-secret'
    value: 'your-microsoft-client-secret-here'  // Replace with actual secret
  }
]
```

#### Environment Variables
```bicep
env: [
  {
    name: 'MICROSOFT_CLIENT_ID'
    value: 'fcfbaf73-654e-49a7-9141-b994192888c6'
  }
  {
    name: 'MICROSOFT_CLIENT_SECRET'
    secretRef: 'microsoft-client-secret'
  }
]
```

### Security Recommendations

#### 1. Use Azure Key Vault (Recommended for Production)
Instead of hardcoding secrets in Bicep, reference Azure Key Vault:

```bicep
// Add Key Vault reference
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  // Key Vault configuration
}

// Reference secret from Key Vault
{
  name: 'microsoft-client-secret'
  keyVaultUrl: '${keyVault.properties.vaultUri}secrets/microsoft-client-secret'
}
```

#### 2. Managed Identity Integration
Configure your Container App to use managed identity for Key Vault access:

```bicep
identity: {
  type: 'SystemAssigned'
}
```

#### 3. Network Security
- Enable private endpoints for Key Vault if handling sensitive data
- Implement network policies to restrict access to authentication endpoints

## Development & Testing

### Local Development Setup

1. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   # Copy and edit .env file
   cp .env.example .env
   # Edit .env with your Microsoft app credentials
   ```

3. **Setup Django database**:
   ```bash
   python manage.py migrate
   python setup_social_app.py
   ```

4. **Start development server**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Testing Authentication Flow

#### Local Testing
- **Login URL**: `http://localhost:8000/accounts/microsoft/login/`
- **Main App**: `http://localhost:8000/`

#### Production Testing
- **Dev Environment**: `https://dev.babelscrib.com/accounts/microsoft/login/`
- **Production**: `https://babelscrib.com/accounts/microsoft/login/`

### Available VS Code Tasks

Use the configured VS Code tasks for easier development:

```bash
# Run Django development server
Ctrl+Shift+P → "Tasks: Run Task" → "Django Runserver"

# View environment variables (debug)
Ctrl+Shift+P → "Tasks: Run Task" → "Log Environment Variables"
```

## Security Best Practices (2025)

### 1. Secret Management
- ✅ **Azure Key Vault**: Store client secrets securely
- ✅ **Managed Identity**: Use system-assigned managed identity for Key Vault access
- ✅ **Secret Rotation**: Implement automated secret rotation policies
- ❌ **Never commit secrets** to version control

### 2. Authentication Security
- ✅ **HTTPS Only**: All authentication endpoints must use HTTPS
- ✅ **CSRF Protection**: Django CSRF middleware enabled
- ✅ **Session Security**: Secure session configuration
- ✅ **Token Validation**: Proper OAuth token validation

### 3. Authorization & Access Control
- ✅ **Principle of Least Privilege**: Request only necessary Microsoft Graph permissions
- ✅ **User Consent**: Implement proper consent flows
- ✅ **Admin Consent**: Consider admin consent for organization-wide deployments

### 4. Monitoring & Logging
- ✅ **Authentication Events**: Log successful and failed authentication attempts
- ✅ **Security Alerts**: Monitor for suspicious authentication patterns
- ✅ **Compliance Logging**: Maintain audit trails for compliance requirements

### 5. Network Security
```bicep
// Example: Container App with network restrictions
properties: {
  configuration: {
    ingress: {
      external: true
      allowInsecure: false  // HTTPS only
      targetPort: 8000
    }
  }
}
```

## Authentication Flow Details

### Standard OAuth 2.0 / OpenID Connect Flow

1. **User Initiation**: User clicks "Continue with Microsoft Entra ID" button
2. **Authorization Request**: Browser redirects to Microsoft authorization endpoint
3. **User Authentication**: User authenticates with Microsoft (MFA if required)
4. **Authorization Grant**: Microsoft redirects back with authorization code
5. **Token Exchange**: Django exchanges authorization code for access/ID tokens
6. **User Creation/Login**: Django creates or updates user account based on token claims
7. **Session Establishment**: User is logged into Django with active session
8. **Application Redirect**: User is redirected to intended application page

### Token Management

#### ID Token Claims (Available in Django)
```json
{
  "aud": "fcfbaf73-654e-49a7-9141-b994192888c6",
  "iss": "https://login.microsoftonline.com/{tenant}/v2.0",
  "sub": "unique-user-identifier",
  "name": "User Display Name",
  "email": "user@domain.com",
  "preferred_username": "user@domain.com"
}
```

#### Django User Model Mapping
- `username` ← `preferred_username` or `email`
- `email` ← `email`
- `first_name` ← `given_name`
- `last_name` ← `family_name`

### Session Management
- Django sessions are used for maintaining user state
- Token refresh handled automatically by django-allauth
- Session timeout configurable in Django settings

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Redirect URI Mismatch (AADSTS50011)
**Error**: `The redirect URI specified in the request does not match the redirect URIs configured for the application`

**Solutions**:
- ✅ Verify exact URL match in Azure AD app registration
- ✅ Ensure trailing slash consistency: `/accounts/microsoft/login/callback/`
- ✅ Check HTTP vs HTTPS protocol matching
- ✅ Validate domain name spelling and case sensitivity

#### 2. Invalid Client Secret (AADSTS7000215)
**Error**: `Invalid client secret provided`

**Solutions**:
- ✅ Regenerate client secret in Azure portal
- ✅ Update environment variables in all environments
- ✅ Run `python update_social_app.py` to update Django configuration
- ✅ Restart application after secret update

#### 3. Application Not Found (AADSTS700016)
**Error**: `Application with identifier was not found`

**Solutions**:
- ✅ Verify `MICROSOFT_CLIENT_ID` matches Azure AD app registration
- ✅ Check that app registration is in correct tenant
- ✅ Ensure app registration is not deleted or disabled

#### 4. SSL/TLS Issues in Development
**Error**: SSL verification errors or mixed content warnings

**Solutions**:
- ✅ Use `python manage.py runserver 0.0.0.0:8000` for local development
- ✅ Configure local development redirect URI: `http://localhost:8000/accounts/microsoft/login/callback/`
- ✅ For HTTPS testing, use ngrok or similar tunneling service

#### 5. Django Allauth Configuration Issues
**Error**: Social app not found or misconfigured

**Solutions**:
```bash
# Reset social app configuration
python setup_social_app.py

# Verify database has correct site configuration
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> Site.objects.get(pk=1)
```

### Debug Commands

#### Check Environment Variables
```bash
python manage.py log_env_vars
```

#### Verify Social App Configuration
```bash
python manage.py shell
>>> from allauth.socialaccount.models import SocialApp
>>> app = SocialApp.objects.get(provider='microsoft')
>>> print(f"Client ID: {app.client_id}")
>>> print(f"Secret: {'*' * len(app.secret)}")
>>> print(f"Sites: {list(app.sites.all())}")
```

#### Test Authentication URLs
```bash
# Development
curl -I http://localhost:8000/accounts/microsoft/login/

# Production
curl -I https://babelscrib.com/accounts/microsoft/login/
```

### Logging and Monitoring

Enable detailed authentication logging in `settings.py`:
```python
LOGGING = {
    'loggers': {
        'allauth': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### Production Deployment Checklist

Before deploying to production:
- [ ] Client secret stored in Azure Key Vault
- [ ] Redirect URIs configured for production domain
- [ ] HTTPS certificates valid and properly configured
- [ ] Environment variables set in Azure Container App
- [ ] Database migrations applied
- [ ] Social app configuration updated
- [ ] Authentication flow tested end-to-end
- [ ] Logging and monitoring configured

### Support Resources

- **Microsoft Entra ID Documentation**: https://docs.microsoft.com/en-us/azure/active-directory/
- **Django Allauth Documentation**: https://django-allauth.readthedocs.io/
- **Azure Container Apps Authentication**: https://docs.microsoft.com/en-us/azure/container-apps/
- **OAuth 2.0 Specification**: https://oauth.net/2/

---

*Last Updated: June 2025*
*Compatible with: Django 4.2+, django-allauth 0.57+, Azure Container Apps*
