# Microsoft Authentication Setup Guide

## Problem
You're getting this error:
```
AADSTS50011: The redirect URI 'https://dev.babelscrib.com/.auth/login/aad/callback' specified in the request does not match the redirect URIs configured for the application 'fcfbaf73-654e-49a7-9141-b994192888c6'.
```

## Root Cause
The error occurs because you're trying to use Azure App Service's Easy Auth, but you're running on Azure Container Apps, which handles authentication differently.

## Solution: Django-based Authentication (Recommended)

I've set up your Django application to handle Microsoft authentication using django-allauth. Here's what was configured:

### 1. Updated Django Settings
- Added `django-allauth` and Microsoft provider to `INSTALLED_APPS`
- Added required middleware: `allauth.account.middleware.AccountMiddleware`
- Configured Microsoft OAuth settings

### 2. Updated URLs
- Added allauth URLs: `path('accounts/', include('allauth.urls'))`

### 3. Updated Requirements
- Added `msal==1.24.0` and `django-allauth==0.57.0`

### 4. Database Migrations
- Ran migrations to create authentication tables

## Required Azure AD Configuration

### Step 1: Update Azure AD App Registration
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Find your app: `fcfbaf73-654e-49a7-9141-b994192888c6`
4. Go to **Authentication**
5. Add these redirect URIs:
   - `https://dev.babelscrib.com/accounts/microsoft/login/callback/`
   - `https://babelscrib.com/accounts/microsoft/login/callback/`
6. Select **Web** as platform type
7. Click **Save**

### Step 2: Get Client Secret
1. In the same app registration, go to **Certificates & secrets**
2. Create a new client secret or use existing one
3. Copy the secret value (you'll need this for environment variables)

## Required Environment Variables

Add these to your environment (`.env` file or Azure configuration):

```env
MICROSOFT_CLIENT_ID=fcfbaf73-654e-49a7-9141-b994192888c6
MICROSOFT_CLIENT_SECRET=your-actual-client-secret-here
```

## Infrastructure Updates

I've updated your `infrastructure/main.bicep` file to include:
- Microsoft Client ID as environment variable
- Microsoft Client Secret as a secure secret reference

**Important**: Replace `'your-microsoft-client-secret-here'` in the Bicep file with the actual secret value or use Azure Key Vault for better security.

## Testing the Setup

1. Install the new packages:
   ```bash
   pip install msal django-allauth
   ```

2. Run migrations (already done):
   ```bash
   python manage.py migrate
   ```

3. Start your development server:
   ```bash
   python manage.py runserver
   ```

4. Visit: `http://localhost:8000/accounts/microsoft/login/`

## Security Best Practices

1. **Use Azure Key Vault** for storing client secrets instead of hardcoding them
2. **Enable HTTPS** for all authentication redirects
3. **Configure proper CORS** settings if needed
4. **Set up proper logging** for authentication events

## Authentication Flow

1. User clicks "Sign in with Microsoft"
2. User is redirected to Microsoft login
3. After successful login, Microsoft redirects to your callback URL
4. Django processes the callback and creates/logs in the user
5. User is redirected to your application

## Troubleshooting

If you still get redirect URI errors:
1. Double-check the redirect URIs in Azure AD exactly match the URLs django-allauth generates
2. Ensure your domain SSL certificates are valid
3. Check that your Container App is accessible at the configured domain

The new authentication flow will work properly with Azure Container Apps and provide better control over the user experience.
