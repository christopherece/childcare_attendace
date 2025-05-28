# Childcare Attendance System

A Django-based web application for managing childcare attendance.

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Run the development server:
```bash
python manage.py runserver
```

5. Access the application at http://localhost:8000
