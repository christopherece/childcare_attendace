import os
import sys
import django
from django.conf import settings
from django.core.management import call_command

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

# Get database settings
DATABASES = settings.DATABASES['default']

# Connect to the database using psycopg2
import psycopg2
conn = psycopg2.connect(
    host=DATABASES['HOST'],
    database=DATABASES['NAME'],
    user=DATABASES['USER'],
    password=DATABASES['PASSWORD']
)
cur = conn.cursor()

try:
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
    
    # Create fresh migrations directory
    migrations_dir = "c:\\Users\\Meztro\\django_prj\\childcare_attendace\\attendance\\migrations_new"
    if os.path.exists(migrations_dir):
        for file in os.listdir(migrations_dir):
            if file.endswith('.py') and file != '__init__.py':
                os.remove(os.path.join(migrations_dir, file))
    
    # Create initial migration
    with open(os.path.join(migrations_dir, '0001_initial.py'), 'w') as f:
        f.write("""
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Center',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('phone', models.CharField(max_length=20)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('capacity', models.IntegerField()),
                ('opening_time', models.TimeField(default='08:30:00')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Parent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Child',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=10)),
                ('allergies', models.TextField(blank=True, null=True)),
                ('medical_conditions', models.TextField(blank=True, null=True)),
                ('emergency_contact', models.CharField(max_length=100)),
                ('emergency_phone', models.CharField(max_length=20)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='child_pix/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(on_delete=models.CASCADE, related_name='children', to='attendance.parent')),
                ('center', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='children', to='attendance.center')),
            ],
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sign_in', models.DateTimeField(blank=True, null=True)),
                ('sign_out', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('child', models.ForeignKey(on_delete=models.CASCADE, to='attendance.child')),
                ('parent', models.ForeignKey(on_delete=models.CASCADE, to='attendance.parent')),
                ('center', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='attendance.center')),
            ],
            options={
                'ordering': ['-sign_in', '-sign_out'],
            },
        ),
    ]
""")
    
    # Fake the migration
    call_command('migrate', 'attendance', '0001_initial', fake=True)
    print("Migration fixed successfully!")

except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
