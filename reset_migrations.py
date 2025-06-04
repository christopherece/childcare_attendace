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

def reset_migrations():
    print("Resetting migrations...")
    
    # Delete all migration records for the attendance app
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM django_migrations WHERE app='attendance'")
        
    print("Migrations reset. You can now run migrations again.")

if __name__ == '__main__':
    reset_migrations()
