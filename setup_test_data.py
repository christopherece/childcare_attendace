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

from django.contrib.auth.models import User
from attendance.models import Center, Teacher, Parent, Child

# Create admin user if it doesn't exist
def create_admin_user():
    print("Creating admin user...")
    try:
        admin_user = User.objects.get(username='admsrv')
        print(f"Admin user {admin_user.username} already exists")
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser(
            username='admsrv',
            email='admin@example.com',
            password='admin123'
        )
        print(f"Created admin user: {admin_user.username}")
    return admin_user

def create_test_data():
    print("\nCreating test data...")
    
    # Create a center
    center = Center.objects.create(
        name="Sunshine Childcare Center",
        address="456 Sunshine Avenue",
        phone="0211234567",
        email="info@sunshinechildcare.com",
        capacity=50,
        opening_time="08:30:00"
    )
    print(f"Created center: {center.name}")
    
    # Create admin user
    admin_user = create_admin_user()
    
    # Create teacher for admin user
    try:
        teacher = Teacher.objects.get(user=admin_user)
        print(f"Teacher {teacher.user.username} already exists")
    except Teacher.DoesNotExist:
        teacher = Teacher.objects.create(
            user=admin_user,
            position="Administrator",
            center=center
        )
        print(f"Created teacher: {teacher.user.username}")
    
    # Create some test children
    print("\nCreating test children...")
    test_children = [
        {"name": "Emma Johnson", "parent": "Sarah Johnson"},
        {"name": "Liam Smith", "parent": "James Smith"},
        {"name": "Olivia Brown", "parent": "Michael Brown"},
        {"name": "Noah Wilson", "parent": "David Wilson"},
        {"name": "Ava Anderson", "parent": "Robert Anderson"}
    ]
    
    for child_data in test_children:
        # Create parent
        parent = Parent.objects.create(
            name=child_data["parent"],
            email=f"{child_data['parent'].lower().replace(' ', '')}@example.com",
            phone=f"021{random.randint(1000000, 9999999)}"
        )
        
        # Create child
        child = Child.objects.create(
            name=child_data["name"],
            parent=parent,
            center=center,
            date_of_birth=datetime.now() - timedelta(days=random.randint(1825, 3650)),  # 5-10 years old
            gender=random.choice(['Male', 'Female', 'Other']),
            emergency_contact=parent.name,
            emergency_phone=parent.phone,
            allergies="None" if random.random() > 0.3 else "Peanut allergy",
            medical_conditions="None" if random.random() > 0.3 else "Asthma"
        )
        print(f"Created child: {child.name} (Parent: {parent.name})")

if __name__ == '__main__':
    create_test_data()
