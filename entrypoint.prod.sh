#!/bin/bash
set -e

echo "Starting BabelScrib production container..."

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

# Set up Site and SocialApp for production
echo "Setting up Site and SocialApp configuration..."
python manage.py setup_production_site --domain "${DOMAIN:-www.babelscrib.com}" --name "${SITE_NAME:-BabelScrib}"

echo "Starting Gunicorn server..."
exec "$@"
