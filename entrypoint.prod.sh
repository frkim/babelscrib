#!/bin/bash
set -e

echo "Starting BabelScrib production container..."
echo "Environment: PRODUCTION"
echo "DEBUG: ${DEBUG:-False}"
echo "DOMAIN: ${DOMAIN:-www.babelscrib.com}"
echo "SITE_NAME: ${SITE_NAME:-www.babelscrib.com}"

# Wait for database to be ready (if using external DB)
echo "Checking database connection..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional)
echo "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created!')
else:
    print('Superuser already exists.')
" || true

# Ensure production site exists with correct domain
echo "Setting up production site configuration..."
echo "Step 1: Adding production site with exact domain..."
python manage.py add_production_site --domain "${DOMAIN:-www.babelscrib.com}" --name "${SITE_NAME:-www.babelscrib.com}"

echo "Step 2: Setting up Microsoft SocialApp for production..."
python manage.py setup_production_site --domain "${DOMAIN:-www.babelscrib.com}" --name "${SITE_NAME:-BabelScrib}" --force-update

echo "Production site configuration completed!"

echo "Starting Gunicorn server..."
exec "$@"
