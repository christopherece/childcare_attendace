import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from django.db import connection
from django.db.utils import ProgrammingError
from django.core.management import call_command

def drop_tables():
    print("Dropping tables...")
    
    # List of tables to drop
    tables = [
        'attendance_child',
        'attendance_parent',
        'attendance_teacher',
        'attendance_center',
        'attendance_attendance',
        'django_migrations',
        'django_content_type',
        'django_admin_log',
        'auth_user',
        'auth_group',
        'auth_permission',
        'auth_user_groups',
        'auth_user_user_permissions',
        'auth_group_permissions',
        'notifications_notification'
    ]
    
    # Drop tables in reverse order of dependencies
    with connection.cursor() as cursor:
        for table in reversed(tables):
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"Dropped table: {table}")
            except ProgrammingError as e:
                print(f"Error dropping {table}: {str(e)}")

def reset_database():
    print("Resetting database...")
    drop_tables()
    call_command('migrate')

if __name__ == '__main__':
    reset_database()
