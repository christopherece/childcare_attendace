# Childcare Attendance System

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![Django 5.2.1](https://img.shields.io/badge/django-5.2.1-blue.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern Django-based web application for managing childcare attendance with real-time tracking, notifications, and comprehensive reporting capabilities.

## 🚀 Features

### 📱 Core Features
- ✅ Real-time attendance tracking with sign-in/sign-out functionality
- ✅ Automatic notifications for parents and staff
- ✅ Late sign-in notifications with customizable reasons
- ✅ Dashboard with live search for children
- ✅ Comprehensive attendance records with historical data
- ✅ Center management with capacity tracking
- ✅ Teacher profiles and assignments
- ✅ Student Monitor with filtering capabilities
- ✅ Room-based attendance tracking
- ✅ Status-based filtering (Present/Absent)
- ✅ Responsive design for mobile and tablet devices

### 👥 User Roles
- 📝 Teachers: 
  - Manage attendance
  - View records
  - Update profiles
  - Monitor students by room
  - Filter attendance by status
- ⚙️ Admin: 
  - Full access to all features
  - System management
  - Center configuration
  - User management

## 📁 Project Structure

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

## 🛠️ Setup Instructions

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Create .env file in project root
# Add the following variables:
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=your-database-url
EMAIL_HOST=your-email-host
EMAIL_PORT=your-email-port
EMAIL_HOST_USER=your-email-user
EMAIL_HOST_PASSWORD=your-email-password
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
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

### 📊 Usage

### 📱 Teacher Login
- Teachers can log in using their credentials
- Dashboard shows all children in their center
- Live search functionality for quick lookup
- Monitor view for room-based attendance tracking
- Filter students by room and attendance status

### 📅 Attendance Management
- Sign-in/Sign-out functionality with timestamps
- Automatic notifications to parents
- Late sign-in tracking with reasons
- Attendance records view with detailed information
- Notes tracking for special attendance circumstances

### 📧 Notifications
- Email notifications for sign-ins and late arrivals
- Customizable notification templates
- Notification history tracking

## 📊 Database Schema

### 📝 Key Models
- Child: Stores child information, parent relationship, and attendance records
- Parent: Contact information and relationship to children
- Attendance: Tracks sign-in/sign-out times, status, and notes
- Center: Childcare center information including capacity and contact details
- Teacher: Staff profiles with center assignments

## 🔐 Security
- All pages require authentication
- Role-based access control
- CSRF protection for forms
- Secure password hashing
- Email verification for notifications

## 🕒 Timezone Handling
- All timestamps are stored in UTC
- Displayed in Pacific/Auckland timezone
- Automatic timezone conversion for user interface

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please open an issue in the GitHub repository.

## 📚 Documentation

- [User Guide](docs/user_guide.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Advanced reporting features
- [ ] Parent portal
- [ ] Analytics dashboard
