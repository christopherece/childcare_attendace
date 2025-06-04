import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

def clean_database():
    print("Cleaning database...")
    
    # Drop all tables in correct order
    with connection.cursor() as cursor:
        # First drop tables that might have foreign key dependencies
        cursor.execute("""
            DROP TABLE IF EXISTS notifications_notification CASCADE;
            DROP TABLE IF EXISTS attendance_attendance CASCADE;
            DROP TABLE IF EXISTS attendance_child CASCADE;
            DROP TABLE IF EXISTS attendance_parent CASCADE;
            DROP TABLE IF EXISTS attendance_center CASCADE;
        """)
        
        # Then drop Django tables
        cursor.execute("""
            DROP TABLE IF EXISTS django_migrations CASCADE;
            DROP TABLE IF EXISTS django_content_type CASCADE;
            DROP TABLE IF EXISTS auth_permission CASCADE;
            DROP TABLE IF EXISTS auth_group CASCADE;
            DROP TABLE IF EXISTS auth_user CASCADE;
            DROP TABLE IF EXISTS django_admin_log CASCADE;
        """)
        
    print("Database cleaned. You can now run migrations again.")

if __name__ == '__main__':
    clean_database()
