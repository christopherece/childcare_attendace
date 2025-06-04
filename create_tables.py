import os
import sys
import psycopg2

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
import django
from django.conf import settings

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

# Create tables manually
sql = """
-- Drop existing tables if they exist
DROP TABLE IF EXISTS attendance_attendance CASCADE;
DROP TABLE IF EXISTS attendance_child CASCADE;
DROP TABLE IF EXISTS attendance_parent CASCADE;
DROP TABLE IF EXISTS attendance_center CASCADE;

-- Create tables
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
    late BOOLEAN DEFAULT FALSE,
    late_reason VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    child_id BIGINT NOT NULL REFERENCES attendance_child(id),
    parent_id BIGINT NOT NULL REFERENCES attendance_parent(id),
    center_id BIGINT REFERENCES attendance_center(id)
);

-- Create indexes
CREATE INDEX idx_attendance_child_parent ON attendance_child(parent_id);
CREATE INDEX idx_attendance_child_center ON attendance_child(center_id);
CREATE INDEX idx_attendance_attendance_child ON attendance_attendance(child_id);
CREATE INDEX idx_attendance_attendance_parent ON attendance_attendance(parent_id);
CREATE INDEX idx_attendance_attendance_center ON attendance_attendance(center_id);
"""

try:
    cur.execute(sql)
    conn.commit()
    print("Tables created successfully!")
except Exception as e:
    print(f"Error creating tables: {e}")
finally:
    cur.close()
    conn.close()
