#!/bin/bash
# Docker entrypoint script for BabelScrib

set -e

echo "Starting BabelScrib..."

# Set Python path to include the app directory
export PYTHONPATH="/app:$PYTHONPATH"

# Run database migrations if needed
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start the application
echo "Starting Django server..."
exec "$@"
