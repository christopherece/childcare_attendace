# Childcare Attendance System

A Django-based web application for managing childcare attendance with features including real-time tracking, notifications, and reporting.

## Features

### Core Features
- Real-time attendance tracking with sign-in/sign-out functionality
- Automatic notifications for parents and staff
- Late sign-in notifications with customizable reasons
- Dashboard with live search for children
- Comprehensive attendance records with historical data
- Center management with capacity tracking
- Teacher profiles and assignments

### User Roles
- Teachers: Manage attendance, view records, and update profiles
- Admin: Full access to all features and system management

## Project Structure

```
childcare_attendace/
├── attendance/           # Main application
│   ├── models.py        # Database models (Child, Parent, Attendance, etc.)
│   ├── views.py         # Application views
│   ├── forms.py         # Forms for data entry
│   └── templates/       # HTML templates
│       └── attendance/
├── notifications/       # Notification system
├── reports/            # Report generation
└── static/             # Static files (CSS, JS, images)
```

## Setup Instructions

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure database settings in `settings.py`:
- PostgreSQL is recommended
- Ensure timezone is set to 'Pacific/Auckland'

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser (for admin access):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Access the application:
- Main application: http://localhost:8000
- Admin panel: http://localhost:8000/admin

## Usage

### Teacher Login
- Teachers can log in using their credentials
- Dashboard shows all children in their center
- Live search functionality for quick lookup

### Attendance Management
- Sign-in/Sign-out functionality with timestamps
- Automatic notifications to parents
- Late sign-in tracking with reasons
- Attendance records view with detailed information

### Notifications
- Email notifications for sign-ins and late arrivals
- Customizable notification templates
- Notification history tracking

## Database Schema

### Key Models
- Child: Stores child information, parent relationship, and attendance records
- Parent: Contact information and relationship to children
- Attendance: Tracks sign-in/sign-out times, status, and notes
- Center: Childcare center information including capacity and contact details
- Teacher: Staff profiles with center assignments

## Security
- All pages require authentication
- Role-based access control
- CSRF protection for forms
- Secure password hashing
- Email verification for notifications

## Timezone Handling
- All timestamps are stored in UTC
- Displayed in Pacific/Auckland timezone
- Automatic timezone conversion for user interface

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository.
