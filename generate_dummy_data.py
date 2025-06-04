import os
import sys
import django
import random
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Parent, Child, Center
from django.contrib.auth.models import User

# Lists of common names
MALE_NAMES = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles',
              'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Donald', 'Mark', 'Paul', 'Steven', 'Andrew', 'Kenneth']

FEMALE_NAMES = ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen',
                'Lisa', 'Nancy', 'Betty', 'Margaret', 'Sandra', 'Ashley', 'Kimberly', 'Donna', 'Carol', 'Michelle']

LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
              'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']

def generate_phone_number():
    return f"021{random.randint(1000000, 9999999)}"

def generate_address():
    streets = ['Main', 'Oak', 'Maple', 'Elm', 'Pine', 'Cedar', 'Walnut', 'Birch', 'Cherry', 'Willow']
    return f"{random.randint(1, 100)} {random.choice(streets)} Street"

def generate_dummy_data():
    print("Generating dummy data...")
    
    # Create a center if it doesn't exist
    center, _ = Center.objects.get_or_create(
        name="Sunshine Childcare Center",
        address="456 Sunshine Avenue",
        phone="0211234567",
        email="info@sunshinechildcare.com",
        capacity=50,
        opening_time="08:30:00"
    )
    
    # Generate 30 dummy child accounts
    for i in range(30):
        # Choose random names
        first_name = random.choice(MALE_NAMES if random.random() > 0.5 else FEMALE_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Generate parent
        parent = Parent.objects.create(
            name=f"{first_name} {last_name}",
            email=f"{first_name.lower()}.{last_name.lower()}@gmail.com",
            phone=generate_phone_number(),
            address=generate_address()
        )
        
        # Generate child
        child = Child.objects.create(
            name=f"{random.choice(MALE_NAMES if random.random() > 0.5 else FEMALE_NAMES)} {last_name}",
            parent=parent,
            center=center,
            date_of_birth=datetime.now() - timedelta(days=random.randint(1825, 3650)),  # 5-10 years old
            gender=random.choice(['Male', 'Female', 'Other']),
            emergency_contact=f"{parent.name} (Parent)",
            emergency_phone=parent.phone,
            allergies="None" if random.random() > 0.3 else random.choice([
                "Peanut allergy",
                "Dairy allergy",
                "Egg allergy",
                "Shellfish allergy",
                "Soy allergy"
            ]),
            medical_conditions="None" if random.random() > 0.3 else random.choice([
                "Asthma",
                "Eczema",
                "Diabetes",
                "Epilepsy",
                "Celiac disease"
            ])
        )
        
        print(f"Created child {i+1}: {child.name}")
    
    print("\nDummy data generation complete!")

if __name__ == '__main__':
    generate_dummy_data()
