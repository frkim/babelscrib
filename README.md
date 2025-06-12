# BabelScrib
Document Translation Web Application

BabelScrib is a Django-based web application that allows users to upload documents and translate them using Azure AI Document Translation services. The application provides a user-friendly interface for file uploads with drag-and-drop functionality and secure document translation powered by Azure Cognitive Services.

## Features

- **Document Upload**: Upload documents to Azure Blob Storage with drag-and-drop interface
- **Document Translation**: Translate documents using Azure AI Document Translation services
- **User Isolation**: Secure user session management with email-based identification
- **Multiple File Formats**: Support for various document formats (PDF, DOCX, PPTX, etc.)
- **Docker Support**: Full containerization for development and production deployments
- **Production Ready**: Configured with security best practices and production settings

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
│   ├── models.py           # Document and UserSession models
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # API endpoints and views
│   ├── urls.py
│   ├── user_utils.py       # User management utilities
│   ├── templates/
│   │   └── upload/
│   │       └── index.html  # Upload interface
│   ├── management/
│   │   └── commands/       # Custom Django commands
│   └── migrations/
├── lib/                    # Reusable service libraries
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── translation_service.py  # Azure translation service wrapper
│   └── django_examples.py
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── upload.js
│   └── images/             # Logos and icons
├── documentation/          # Project documentation
├── requirements.txt        # Python dependencies
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
   Create a `.env` file in the project root with the following variables:
   ```env
   # Django Configuration
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   
   # Azure Storage Configuration
   AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
   AZURE_STORAGE_CONTAINER_NAME=documents
   
   # Azure Translation Configuration
   AZURE_TRANSLATION_KEY=your-translation-service-key
   AZURE_TRANSLATION_ENDPOINT=https://your-region.api.cognitive.microsofttranslator.com/
   AZURE_TRANSLATION_REGION=your-region
   
   # Optional: Database Configuration (defaults to SQLite)
   # DATABASE_URL=postgres://user:password@localhost:5432/babelscrib
   ```

5. **Run Database Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser (Optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Development Server**
   ```bash
   python manage.py runserver
   ```

### Docker Development Setup

1. **Build and Run with Docker**
   ```bash
   # Development (using latest tag)
   docker build -t babelscrib:latest .
   docker run -p 8000:8000 --env-file .env babelscrib:latest
   
   # Or use the provided scripts
   ./docker_build_run_dev.sh  # Linux/macOS
   docker_build_run_dev.cmd   # Windows
   ```

### Production Deployment

1. **Build Production Container**
   ```bash
   docker build -f Dockerfile.prod -t babelscrib:prod .
   ```

2. **Deploy to Azure Container Apps** (recommended)
   - See `documentation/AZURE_REGISTRY_COMMANDS.md` for detailed deployment instructions
   - Configure environment variables in Azure portal or deployment template

## Usage

1. **Access the Application**
   - Navigate to `http://127.0.0.1:8000/upload/` in your web browser
   - Enter your email address to create a session

2. **Upload Documents**
   - Use the drag-and-drop interface or click to select files
   - Supported formats: PDF, DOCX, PPTX, TXT, and more
   - Files are securely uploaded to Azure Blob Storage

3. **Translate Documents**
   - Select uploaded documents from your list
   - Choose target language for translation
   - Azure AI will process and translate your documents

4. **Download Results**
   - Access translated documents from the interface
   - Original and translated files are preserved separately

## API Endpoints

- `GET /upload/` - Main upload interface
- `POST /upload/api/upload/` - Upload document endpoint
- `GET /upload/api/documents/` - List user documents
- `POST /upload/api/translate/` - Translate document endpoint
- `GET /upload/api/download/<id>/` - Download document

## Architecture

The application uses a multi-tier architecture:

- **Frontend**: Django templates with JavaScript for upload interface
- **Backend**: Django REST framework for API endpoints
- **Storage**: Azure Blob Storage for document persistence
- **Translation**: Azure AI Document Translation services
- **Database**: SQLite (development) / PostgreSQL (production)
- **Security**: User isolation through email-based sessions

## Key Dependencies

- **Django 4.2+**: Web framework
- **Django REST Framework**: API development
- **Azure Storage Blob**: Document storage
- **Azure AI Translation**: Document translation services
- **Azure Identity**: Authentication for Azure services
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

- **User Isolation**: Documents are isolated by user email sessions
- **Secure File Handling**: Files are validated and securely stored
- **Environment Variables**: Sensitive configuration stored in environment variables
- **Production Settings**: Separate configuration for production deployment
- **CSRF Protection**: Built-in Django CSRF protection
- **Static File Security**: WhiteNoise for secure static file serving

## Documentation

Additional documentation is available in the `documentation/` folder:

- `IMPLEMENTATION_SUMMARY.md`: Technical implementation details
- `TRANSLATION_FEATURE.md`: Translation service documentation
- `USER_ISOLATION_SECURITY.md`: Security implementation details
- `PRODUCTION_SECURITY.md`: Production security guidelines
- `AZURE_REGISTRY_COMMANDS.md`: Azure deployment commands
- `DOCKER_SCRIPTS_README.md`: Docker usage instructions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Azure Connection Errors**: Verify your Azure credentials and connection strings
2. **File Upload Failures**: Check Azure Blob Storage permissions and container existence
3. **Translation Errors**: Ensure Azure Cognitive Services is properly configured
4. **Static Files Not Loading**: Run `python manage.py collectstatic` for production

### Logs

Check `debug.log` for application logs and error details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.