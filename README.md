# BabelScrib
Anonymous Document Translation Web Application

BabelScrib is a Django-based web application that allows anonymous users to upload documents and translate them using Azure AI Document Translation services. The application provides a user-friendly interface for file uploads with drag-and-drop functionality and document translation powered by Azure Cognitive Services.

## ⚠️ Important: Anonymous Access

**BabelScrib operates without authentication** - all uploaded files are accessible to all users. This is a public file sharing and translation service suitable for non-sensitive documents.

## Quick Start

For a rapid deployment experience:

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd babelscrib
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

2. **Run with Docker** (recommended):
   ```bash
   docker build -t babelscrib .
   docker run -p 8000:8000 --env-file .env babelscrib
   ```

3. **Access**: Open `http://localhost:8000/`

For detailed setup instructions, see the [Setup Instructions](#setup-instructions) section below.

## Features

- **Anonymous Document Upload**: Upload documents to Azure Blob Storage with drag-and-drop interface (no registration required)
- **Document Translation**: Translate documents using Azure AI Document Translation services
- **Public File Access**: All users can access all uploaded files
- **Multiple File Formats**: Support for various document formats (PDF, DOCX, PPTX, etc.)
- **Docker Support**: Full containerization for development and production deployments
- **Production Ready**: Configured with security best practices for anonymous access

## Project Structure

```
babelscrib/
├── api/                    # Django project configuration
│   ├── __init__.py
│   ├── settings.py         # Main Django settings
│   ├── build_settings.py   # Build-specific settings
│   ├── urls.py             # URL routing
│   ├── wsgi.py
│   └── asgi.py
├── upload/                 # Main upload application
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py           # Document model (simplified)
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # API endpoints and views
│   ├── urls.py
│   ├── middleware.py       # HTTPS middleware
│   ├── templates/
│   │   └── upload/
│   │       └── index.html  # Upload interface
│   ├── management/
│   │   └── commands/       # Custom Django commands
│   └── migrations/
├── services/               # Reusable service libraries
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── translation_service.py  # Azure translation service wrapper
│   └── README.md
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── upload.js
│   └── images/             # Logos and icons
├── documentation/          # Project documentation
├── infrastructure/        # Azure infrastructure as code
│   └── main.bicep         # Azure Bicep template for deployment
├── .github/               # GitHub Actions workflows
│   └── workflows/         # CI/CD pipelines
├── .env.example           # Environment configuration template
├── requirements.txt       # Python dependencies
├── manage.py              # Django management script
├── Dockerfile             # Development container
├── Dockerfile.prod        # Production container
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Azure account with Blob Storage and Cognitive Services (Document Translation)
- Docker (optional, for containerized deployment)

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd babelscrib
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # source .venv/bin/activate  # On macOS/Linux
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Copy the example environment file and configure your Azure credentials:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file with your Azure credentials:
   ```env
   # Django Configuration
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   
   # Azure Translation Service Configuration
   AZURE_TRANSLATION_KEY=your_azure_translation_key_here
   AZURE_TRANSLATION_ENDPOINT=https://your-translator.cognitiveservices.azure.com
   
   # Azure Storage Configuration
   AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string_here
   AZURE_STORAGE_CONTAINER_NAME_SOURCE=source
   AZURE_STORAGE_CONTAINER_NAME_TARGET=target
   
   # Azure Blob Storage URIs (for translation service)
   AZURE_TRANSLATION_SOURCE_URI=https://yourstorageaccount.blob.core.windows.net/source
   AZURE_TRANSLATION_TARGET_URI=https://yourstorageaccount.blob.core.windows.net/target
   ```

5. **Run Database Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser (Optional - Not Required)**
   ```bash
   # Note: Admin interface is not available since authentication was removed
   # This step can be skipped
   python manage.py createsuperuser
   ```

7. **Start the Development Server**
   ```bash
   python manage.py runserver
   ```

   The application will be available at `http://127.0.0.1:8000/`

### Docker Development Setup

1. **Build and Run with Docker**
   ```bash
   # Development (using latest tag)
   docker build -t babelscrib:latest .
   docker run -p 8000:8000 --env-file .env babelscrib:latest
   ```

2. **Using Provided Scripts**
   The project includes convenience scripts for common Docker operations:
   
   **Linux/macOS:**
   ```bash
   ./docker_build_run_dev.sh    # Build and run development container
   ./docker_build_run_prod.sh   # Build and run production container
   ./docker_build_push_dev.sh   # Build and push to registry (dev)
   ./docker_build_push_prod.sh  # Build and push to registry (prod)
   ```
   
   **Windows:**
   ```cmd
   docker_build_run_dev.cmd     # Build and run development container
   docker_build_run_prod.cmd    # Build and run production container
   docker_build_push_dev.cmd    # Build and push to registry (dev)
   docker_build_push_prod.cmd   # Build and push to registry (prod)
   ```

### Production Deployment

#### Option 1: Azure Container Apps (Recommended)

1. **Deploy Infrastructure**
   ```bash
   # Deploy Azure infrastructure using Bicep
   az deployment group create \
     --resource-group your-resource-group \
     --template-file infrastructure/main.bicep \
     --parameters location=westeurope
   ```

2. **Use GitHub Actions for CI/CD**
   - The project includes GitHub Actions workflows for automated deployment
   - Configure repository secrets for Azure credentials
   - Push to trigger automated builds and deployments

#### Option 2: Manual Docker Deployment

1. **Build Production Container**
   ```bash
   docker build -f Dockerfile.prod -t babelscrib:prod .
   ```

2. **Deploy to Azure Container Registry**
   - See `documentation/AZURE_REGISTRY_COMMANDS.md` for detailed deployment instructions
   - Configure environment variables in Azure portal or deployment template

## Usage

1. **Access the Application**
   - Navigate to `http://127.0.0.1:8000/` in your web browser
   - No registration or email required - completely anonymous

2. **Upload Documents**
   - Use the drag-and-drop interface or click to select files
   - Supported formats: PDF, DOCX, PPTX, TXT, and more
   - Files are uploaded to Azure Blob Storage and accessible to all users

3. **Translate Documents**
   - Click "Launch Translation Process" after uploading files
   - Choose target language for translation
   - Azure AI will process and translate all uploaded documents

4. **Download Results**
   - Access translated documents from the interface
   - All users can download any uploaded or translated files
   - Translated files are automatically deleted after download

## API Endpoints

- `GET /` - Main upload interface
- `POST /upload/` - Upload document endpoint
- `GET /list-files/` - List all uploaded documents (global)
- `POST /translate/` - Translate all documents endpoint
- `GET /download/<filename>/` - Download any document
- `GET /test-storage/` - Storage configuration test endpoint

## CI/CD and Deployment

### GitHub Actions Workflows

The project includes several GitHub Actions workflows for automated deployment:

- **`infrastructure-deploy.yml`**: Deploys Azure infrastructure using Bicep templates
- **`docker-build_deploy-dev.yml`**: Builds and deploys development environment
- **`docker-build_deploy-prod.yml`**: Builds and deploys production environment  
- **`full-deployment.yml`**: Complete infrastructure and application deployment

### Azure Infrastructure

The `infrastructure/` folder contains Azure Bicep templates for:
- **Container Apps Environment**: Managed containerized hosting
- **Container Registry**: Private Docker image storage
- **Storage Account**: Document storage with blob containers
- **Log Analytics**: Application monitoring and logging
- **Azure Translator**: Document translation services
- **Managed Identity**: Secure Azure service authentication

## Architecture

The application uses a simplified architecture for anonymous access:

- **Frontend**: Django templates with JavaScript for upload interface
- **Backend**: Django with simplified views for anonymous access
- **Storage**: Azure Blob Storage for document persistence (public access)
- **Translation**: Azure AI Document Translation services
- **Database**: SQLite (development) / PostgreSQL (production) - simplified schema
- **Infrastructure**: Azure Container Apps with managed scaling
- **Monitoring**: Azure Log Analytics and Application Insights

## Key Dependencies
- **Django**: Web framework
- **Azure Storage Blob**: Document storage
- **Azure AI Translation**: Document translation services
- **Gunicorn**: Production WSGI server
- **WhiteNoise**: Static file serving

## Development

### Available Django Management Commands

```bash
# Run the development server
python manage.py runserver

# Log environment variables (useful for debugging)
python manage.py log_env_vars

# Run database migrations
python manage.py migrate

# Create database migrations
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser
```

### VS Code Tasks

The project includes VS Code tasks for common operations:
- **Django Runserver**: Start the development server
- **Log Environment Variables**: Debug environment configuration

## Security Features

⚠️ **Important Security Notice**: BabelScrib operates without user authentication

- **Anonymous Access**: All files are accessible to all users
- **No User Isolation**: Files are not isolated between users
- **Public File Sharing**: Suitable for non-sensitive documents only
- **Environment Variables**: Sensitive configuration stored in environment variables
- **Production Settings**: Separate configuration for production deployment
- **CSRF Protection**: Built-in Django CSRF protection for forms
- **Static File Security**: WhiteNoise for secure static file serving
- **Rate Limiting**: Recommended for production to prevent abuse

## Documentation

Additional documentation is available in the `documentation/` folder:

- `README.md`: Complete system overview and architecture
- `IMPLEMENTATION_SUMMARY.md`: Authentication removal process details
- `TRANSLATION_FEATURE.md`: Translation service documentation
- `PRODUCTION_SECURITY.md`: Security considerations for anonymous access
- `AZURE_REGISTRY_COMMANDS.md`: Azure deployment commands
- `DOCKER_SCRIPTS_README.md`: Docker usage instructions
- `AZURE_STORAGE_TROUBLESHOOTING.md`: Storage troubleshooting guide

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Azure Connection Errors**: 
   - Verify your Azure credentials in the `.env` file
   - Ensure your Azure Storage account and containers exist
   - Check that your Azure Translator service is active

2. **File Upload Failures**: 
   - Check Azure Blob Storage permissions and container existence
   - Verify `AZURE_STORAGE_CONNECTION_STRING` is correct
   - Ensure source and target containers are created in Azure Storage

3. **Translation Errors**: 
   - Ensure Azure Cognitive Services Translator is properly configured
   - Verify your translation endpoint and key are correct
   - Check that the target language is supported by Azure Translator

4. **Static Files Not Loading**: 
   - Run `python manage.py collectstatic` for production
   - Check that `whitenoise` is configured correctly in Django settings

5. **Docker Issues**:
   - Ensure Docker is running and accessible
   - Check that the `.env` file is present and correctly formatted
   - Verify port 8000 is not already in use

### Logs and Debugging

- **Application Logs**: Check `debug.log` for application logs and error details
- **Container Logs**: Use `docker logs <container-id>` for container-specific issues
- **Azure Logs**: Monitor Azure Container Apps logs through the Azure portal
- **Django Debug**: Set `DEBUG=True` in your `.env` file for development debugging

### Getting Help

- Check the `documentation/` folder for detailed guides
- Review Azure service status if experiencing connectivity issues
- Ensure all required environment variables are set correctly

## License

This project is licensed under the MIT License - see the LICENSE file for details.