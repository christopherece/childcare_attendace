import os
import sys
import django
import psycopg2

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

def clean_database():
    print("Cleaning database...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host='192.168.10.42',
            user='postgres',
            password='Mmsucit1502',
            database='postgres'  # Connect to default database
        )
        
        # Enable autocommit for database operations
        conn.autocommit = True
        cursor = conn.cursor()
        
        try:
            # Drop and recreate the database
            cursor.execute("DROP DATABASE IF EXISTS funtime_tbl;")
            cursor.execute("CREATE DATABASE funtime_tbl;")
            print("Database reset successfully")
        except Exception as e:
            print(f"Error resetting database: {str(e)}")
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

if __name__ == '__main__':
    clean_database()
