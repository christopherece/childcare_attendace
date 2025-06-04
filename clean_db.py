import os
import sys
import django
from django.db import connections, transaction
from django.db.utils import load_backend

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

def clean_database():
    print("Cleaning database...")
    
    # Get database connection
    db_config = connections['default'].settings_dict
    backend = load_backend(db_config['ENGINE'])
    
    # Connect to PostgreSQL
    conn = backend.DatabaseWrapper({
        'NAME': 'postgres',  # Connect to default database
        'USER': db_config['USER'],
        'PASSWORD': db_config['PASSWORD'],
        'HOST': db_config['HOST'],
        'PORT': db_config['PORT'],
    }, 'default')
    
    # Drop and recreate the database
    with transaction.atomic():
        with conn.cursor() as cursor:
            try:
                cursor.execute("DROP DATABASE IF EXISTS funtime_tbl;")
                cursor.execute("CREATE DATABASE funtime_tbl;")
                print("Database reset successfully")
            except Exception as e:
                print(f"Error resetting database: {str(e)}")

if __name__ == '__main__':
    clean_database()
