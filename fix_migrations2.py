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
    
    # Drop all existing tables
    cur.execute("""
        DROP TABLE IF EXISTS attendance_attendance CASCADE;
        DROP TABLE IF EXISTS attendance_child CASCADE;
        DROP TABLE IF EXISTS attendance_parent CASCADE;
        DROP TABLE IF EXISTS attendance_center CASCADE;
    """)
    
    # Create tables without the late fields
    cur.execute("""
        CREATE TABLE attendance_center (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            address TEXT NOT NULL,
            phone VARCHAR(20) NOT NULL,
            email VARCHAR(254) UNIQUE NOT NULL,
            capacity INTEGER NOT NULL,
            opening_time TIME NOT NULL DEFAULT '08:30:00',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE attendance_parent (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(254) UNIQUE NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE attendance_child (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            date_of_birth DATE NOT NULL,
            gender VARCHAR(10) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
            allergies TEXT,
            medical_conditions TEXT,
            emergency_contact VARCHAR(100) NOT NULL,
            emergency_phone VARCHAR(20) NOT NULL,
            profile_picture VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            parent_id BIGINT NOT NULL REFERENCES attendance_parent(id),
            center_id BIGINT REFERENCES attendance_center(id)
        );

        CREATE TABLE attendance_attendance (
            id BIGSERIAL PRIMARY KEY,
            sign_in TIMESTAMP WITH TIME ZONE,
            sign_out TIMESTAMP WITH TIME ZONE,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            child_id BIGINT NOT NULL REFERENCES attendance_child(id),
            parent_id BIGINT NOT NULL REFERENCES attendance_parent(id),
            center_id BIGINT REFERENCES attendance_center(id)
        );
    """)
    
    conn.commit()
    print("Database tables recreated successfully!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
