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
conn = psycopg2.connect(
    host=DATABASES['HOST'],
    database=DATABASES['NAME'],
    user=DATABASES['USER'],
    password=DATABASES['PASSWORD']
)
cur = conn.cursor()

try:
    # Remove the columns
    cur.execute("""
        ALTER TABLE attendance_attendance 
        DROP COLUMN IF EXISTS late,
        DROP COLUMN IF EXISTS late_reason;
    """)
    conn.commit()
    print("Columns removed successfully!")
except Exception as e:
    print(f"Error removing columns: {e}")
finally:
    cur.close()
    conn.close()
