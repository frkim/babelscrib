# babelscrib
Translation Web App


#  Document Upload

This project is a Django web API that allows users to upload documents to Azure Blob Storage. It provides a user-friendly web interface for file uploads, supporting both drag-and-drop and file selection from the local computer.

## Project Structure

```
django-azure-upload
├── api
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── upload
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── templates
│       └── upload
│           └── index.html
├── static
│   ├── css
│   │   └── style.css
│   └── js
│       └── upload.js
├── requirements.txt
├── main.py
├── .env.example
└── README.md
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd django-azure-upload
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   - Copy `.env.example` to `.env` and update the Azure Blob Storage connection string:
     ```
     AZURE_STORAGE_CONNECTION_STRING=<your_connection_string>
     ```

5. **Run Migrations**
   ```bash
   python main.py migrate
   ```

6. **Start the Development Server**
   ```bash
   python main.py runserver
   ```

## Usage

- Navigate to `http://127.0.0.1:8000/upload/` in your web browser.
- Use the provided interface to upload documents to Azure Blob Storage.

## Dependencies

- Django
- Azure Storage SDK

## License

This project is licensed under the MIT License.