# Docker Setup for BabelScrib

This document explains how to run BabelScrib using Docker.

## Quick Start

### Development

1. **Clone and navigate to the project:**
   ```bash
   cd d:\work\202506_BabelScrib\babelscrib
   ```

2. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with your Azure credentials.

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Open http://localhost:8000

### Production

1. **Copy environment variables:**
   ```bash
   cp .env.example .env.prod
   ```
   Edit `.env.prod` with production values.

2. **Run production stack:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

3. **Access the application:**
   - HTTP: http://localhost
   - HTTPS: https://localhost (after SSL setup)

## Files Created

### Core Docker Files
- **Dockerfile**: Multi-stage build for the Django application
- **.dockerignore**: Excludes unnecessary files from Docker context
- **docker-compose.yml**: Development environment
- **docker-compose.prod.yml**: Production environment with PostgreSQL and Nginx
- **nginx.conf**: Production-ready Nginx configuration

### Key Features

#### Dockerfile
- Based on Python 3.12 slim
- Non-root user for security
- Health checks included
- Static files collection
- Optimized for production

#### Development Stack
- Django development server
- SQLite database
- Volume mounting for live code changes
- Port 8000 exposed

#### Production Stack
- Django with Gunicorn (ready for extension)
- PostgreSQL database
- Nginx reverse proxy
- Redis for caching
- SSL/HTTPS ready
- Health checks for all services

## Environment Variables

Required variables (copy from `.env.example`):

```env
# Azure Configuration
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
AZURE_TRANSLATOR_KEY=your-translator-key
AZURE_TRANSLATOR_ENDPOINT=your-translator-endpoint

# Django Configuration
SECRET_KEY=your-secret-key
DEBUG=0  # Set to 1 for development
```

## Docker Commands

### Development
```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build web
```

### Production
```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Scale web service
docker-compose -f docker-compose.prod.yml up --scale web=3 -d

# View production logs
docker-compose -f docker-compose.prod.yml logs -f web

# Update and restart
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Maintenance
```bash
# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py createsuperuser

# Database backup (production)
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres babelscrib > backup.sql

# Database restore (production)
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres babelscrib < backup.sql
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files with real credentials
2. **SSL/HTTPS**: Configure SSL certificates in production
3. **Database**: Use strong passwords for PostgreSQL
4. **File Upload**: 40MB limit configured in Nginx
5. **Headers**: Security headers configured in Nginx

## Networking

### Development Ports
- **8000**: Django application

### Production Ports
- **80**: HTTP (Nginx)
- **443**: HTTPS (Nginx, after SSL setup)
- **5432**: PostgreSQL (internal)
- **6379**: Redis (internal)

## Volumes

### Development
- Code mounted as volume for live changes
- Static files volume
- Media files volume

### Production
- Persistent PostgreSQL data
- Static files served by Nginx
- Media files served by Nginx

## Health Checks

All services include health checks:
- **Web**: HTTP GET to application root
- **Database**: PostgreSQL connection check
- **Redis**: Redis ping command
- **Nginx**: Depends on web service

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose files
2. **Permission issues**: Check file permissions and user ownership
3. **Memory issues**: Increase Docker memory limits
4. **Azure connection**: Verify environment variables

### Debugging
```bash
# Check service status
docker-compose ps

# Inspect specific service
docker-compose logs web

# Shell into container
docker-compose exec web bash

# Check disk usage
docker system df
docker system prune  # Clean up unused resources
```

## Performance Optimization

1. **Multi-stage builds**: Dockerfile uses optimized Python image
2. **Layer caching**: Dependencies installed before code copy
3. **Static files**: Served directly by Nginx in production
4. **Gzip compression**: Enabled in Nginx
5. **Connection pooling**: Ready for database connection pooling

This Docker setup provides a complete, production-ready environment for the BabelScrib document translation application.
