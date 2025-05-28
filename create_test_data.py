import os
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Parent, Child, Attendance

def generate_random_name():
    first_names = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Jessica', 'Daniel', 'Olivia', 'Matthew', 'Sophia',
                 'Andrew', 'Ava', 'William', 'Emma', 'James', 'Mia', 'Benjamin', 'Charlotte', 'Alexander', 'Amelia']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_random_email():
    return f"{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"

def generate_random_phone():
    return ''.join(random.choices(string.digits, k=10))

def generate_random_address():
    street_names = ['Main', 'Oak', 'Maple', 'Pine', 'Cedar', 'Elm', 'Spruce', 'Birch', 'Willow', 'Chestnut']
    return f"{random.randint(1, 999)} {random.choice(street_names)} St, City {random.randint(10000, 99999)}"

def generate_random_date_of_birth():
    return timezone.now() - timedelta(days=random.randint(365, 365*10))

def create_test_data():
    # Create 10 parents
    parents = []
    for _ in range(10):
        parent = Parent.objects.create(
            name=generate_random_name(),
            email=generate_random_email(),
            phone=generate_random_phone(),
            address=generate_random_address(),
        )
        parents.append(parent)
    
    # Create 30 children (3 per parent)
    for parent in parents:
        for _ in range(3):
            child = Child.objects.create(
                name=generate_random_name(),
                date_of_birth=generate_random_date_of_birth(),
                gender=random.choice(['Male', 'Female', 'Other']),
                allergies=' '.join(random.choices(['Nuts', 'Dairy', 'Eggs', 'Pollen'], k=random.randint(0, 3))),
                medical_conditions=' '.join(random.choices(['Asthma', 'Diabetes', 'Eczema'], k=random.randint(0, 2))),
                emergency_contact=generate_random_name(),
                emergency_phone=generate_random_phone(),
                parent=parent,
            )
            
            # Create one attendance record per day for the last 30 days
            for day in range(30):
                # Only create a record if there isn't one for this day already
                if not Attendance.objects.filter(
                    child=child,
                    created_at__date=timezone.now() - timedelta(days=day)
                ).exists():
                    Attendance.objects.create(
                        child=child,
                        parent=parent,
                        timestamp=timezone.now() - timedelta(days=day)
                    )

if __name__ == '__main__':
    create_test_data()
