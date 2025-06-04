import os
import sys
import django
from django.conf import settings
import psycopg2

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

# Get database settings
DATABASES = settings.DATABASES['default']

# Connect to the database
try:
    conn = psycopg2.connect(
        host=DATABASES['HOST'],
        database=DATABASES['NAME'],
        user=DATABASES['USER'],
        password=DATABASES['PASSWORD']
    )
    cur = conn.cursor()
    
    # Drop the late fields
    cur.execute("""
        ALTER TABLE attendance_attendance 
        DROP COLUMN IF EXISTS late,
        DROP COLUMN IF EXISTS late_reason;
    """)
    
    conn.commit()
    print("Late fields removed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
