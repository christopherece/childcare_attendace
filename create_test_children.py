import os
import django
import random
from datetime import datetime, timedelta

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Child, Parent, Center

# Get or create a center
try:
    center = Center.objects.first()
    if not center:
        center = Center.objects.create(
            name="Sunshine Early Learning Center",
            address="123 Sunshine Ave",
            phone="09 876 5432",
            email="info@sunshinelearning.co.nz",
            capacity=50
        )
except Exception as e:
    print(f"Error creating center: {e}")
    exit(1)

# Create realistic parent names
parents = [
    "Sarah Johnson",
    "Michael Williams",
    "Emma Brown",
    "David Smith",
    "Sophie Taylor",
    "James Wilson",
    "Olivia Anderson",
    "Thomas White",
    "Grace Martin",
    "William Thompson"
]

# Create realistic child names
male_names = [
    "Oliver",
    "James",
    "William",
    "Henry",
    "Max",
    "Ben",
    "Charlie",
    "Tom",
    "Luke",
    "Jack"
]

female_names = [
    "Emma",
    "Olivia",
    "Sophie",
    "Charlotte",
    "Amelia",
    "Lily",
    "Mia",
    "Isabella",
    "Ava",
    "Grace"
]

# Create parents
for parent_name in parents:
    try:
        parent = Parent.objects.create(
            name=parent_name,
            email=f"{parent_name.lower().replace(' ', '_')}@gmail.com",
            phone=f"021 {random.randint(1000000, 9999999)}"
        )
        print(f"Created parent: {parent_name}")
    except Exception as e:
        print(f"Error creating parent {parent_name}: {e}")
        continue

# Create 20 test children with realistic names
for i in range(1, 21):
    try:
        # Generate random birth date (between 1 and 5 years ago)
        days_offset = random.randint(365, 1825)
        birth_date = datetime.now() - timedelta(days=days_offset)
        
        # Choose random parent
        parent = random.choice(Parent.objects.all())
        
        # Choose random gender and name
        gender = random.choice(['Male', 'Female'])
        if gender == 'Male':
            name = f"{random.choice(male_names)} {parent.name.split()[-1]}"
        else:
            name = f"{random.choice(female_names)} {parent.name.split()[-1]}"
            
        # Add random medical conditions (20% chance)
        medical_conditions = None
        if random.random() < 0.2:
            medical_conditions = random.choice([
                "Asthma",
                "Eczema",
                "Food allergies",
                "Diabetes",
                "Seizure disorder"
            ])
            
        # Add random allergies (20% chance)
        allergies = None
        if random.random() < 0.2:
            allergies = random.choice([
                "Peanuts",
                "Dairy",
                "Eggs",
                "Soy",
                "Wheat"
            ])

        # Create child
        child = Child.objects.create(
            name=name,
            parent=parent,
            center=center,
            date_of_birth=birth_date,
            gender=gender,
            allergies=allergies,
            medical_conditions=medical_conditions,
            emergency_contact="Emma Brown",
            emergency_phone="021 1234567"
        )
        
        print(f"Created child {i}: {name} (Parent: {parent.name})")
    except Exception as e:
        print(f"Error creating child {i}: {e}")

print("\nAll test children have been created!")
