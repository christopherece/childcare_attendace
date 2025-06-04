import os
import sys
import django
from django.db import connections

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

def drop_tables():
    print("Dropping tables...")
    
    # Get the database connection
    conn = connections['default']
    
    # List of tables to drop
    tables = [
        'attendance_child',
        'attendance_parent',
        'attendance_teacher',
        'attendance_center',
        'attendance_attendance',
        'notifications_notification',
        'django_migrations',
        'django_content_type',
        'django_admin_log',
        'auth_user',
        'auth_group',
        'auth_permission',
        'auth_user_groups',
        'auth_user_user_permissions',
        'auth_group_permissions',
        'django_session'
    ]
    
    # Drop tables in reverse order of dependencies
    with conn.cursor() as cursor:
        for table in reversed(tables):
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"Dropped table: {table}")
            except Exception as e:
                print(f"Error dropping {table}: {str(e)}")

if __name__ == '__main__':
    drop_tables()
