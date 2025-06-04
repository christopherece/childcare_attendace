import os
import sys
import django
import random
from datetime import datetime, timedelta
import names

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Center, Teacher, Parent, Child, Room

# Common street names for addresses
STREET_NAMES = [
    "Baker Street", "Churchill Avenue", "Daisy Lane", "Elm Street", "Franklin Road",
    "Garden Street", "Hillside Avenue", "Ivy Lane", "Jasper Street", "King Road"
]

# Common suburbs
SUBURBS = [
    "Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga",
    "Dunedin", "Napier", "Palmerston North", "New Plymouth", "Whangarei"
]

# Common allergies
ALLERGIES = [
    "None", "Peanut allergy", "Dairy allergy", "Egg allergy", "Tree nut allergy"
]

# Common medical conditions
MEDICAL_CONDITIONS = [
    "None", "Asthma", "Eczema", "Diabetes", "Epilepsy"
]

def create_dummy_children():
    print("Creating dummy children and parents...")
    
    # Create or get the center
    center, created = Center.objects.get_or_create(
        name="Sunshine Childcare Center",
        defaults={
            'address': "456 Sunshine Avenue",
            'phone': "0211234567",
            'email': "info@sunshinechildcare.com",
            'capacity': 50,
            'opening_time': "08:30:00"
        }
    )
    
    # Create rooms if they don't exist
    rooms = []
    for age_range in ["2-3 years", "3-4 years", "4-5 years", "5-6 years"]:
        room, created = Room.objects.get_or_create(
            name=f"Room {age_range}",
            center=center,
            defaults={
                'capacity': 15,
                'age_range': age_range,
                'description': f"Room for children aged {age_range}"
            }
        )
        rooms.append(room)
    
    # Create 30 children with realistic data
    for i in range(30):
        # Generate random child data
        child_gender = random.choice(['Male', 'Female'])
        child_name = names.get_full_name(gender='male' if child_gender == 'Male' else 'female')
        
        # Generate random parent data
        parent_gender = random.choice(['Male', 'Female'])
        parent_name = names.get_full_name(gender='male' if parent_gender == 'Male' else 'female')
        
        # Create parent
        parent = Parent.objects.create(
            name=parent_name,
            email=f"{parent_name.lower().replace(' ', '')}@example.com",
            phone=f"021{random.randint(1000000, 9999999)}",
            address=f"{random.randint(1, 100)} {random.choice(STREET_NAMES)}, {random.choice(SUBURBS)}"
        )
        
        # Create child
        child = Child.objects.create(
            name=child_name,
            parent=parent,
            center=center,
            room=random.choice(rooms),  # Assign to a random room
            date_of_birth=datetime.now() - timedelta(days=random.randint(1825, 3650)),  # 5-10 years old
            gender=child_gender,
            emergency_contact=parent_name,
            emergency_phone=parent.phone,
            allergies=random.choice(ALLERGIES),
            medical_conditions=random.choice(MEDICAL_CONDITIONS)
        )
        
        print(f"Created child: {child.name} (Parent: {parent.name}, Room: {child.room.name})")

if __name__ == '__main__':
    create_dummy_children()
