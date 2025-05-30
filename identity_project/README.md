# Identity Project

A Django-based identity management system.

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Start the development server: `python manage.py runserver`

## Environment Variables

- `DJANGO_SECRET_KEY`: Secret key for Django
- `DJANGO_DEBUG`: Set to 'True' for development, 'False' for production
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts