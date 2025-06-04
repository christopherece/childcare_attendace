import os
import sys
import django
import random
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Child, Center, Teacher
from django.contrib.auth.models import User

# Get the admin user
try:
    admin_user = User.objects.get(username='admsrv')
    print(f"Admin user found: {admin_user.username}")
except User.DoesNotExist:
    print("Admin user not found!")
    exit()

# Create a teacher for the admin user if one doesn't exist
try:
    teacher = Teacher.objects.get(user=admin_user)
    print(f"Teacher found: {teacher.user.username}")
except Teacher.DoesNotExist:
    print("Creating teacher for admin user...")
    teacher = Teacher.objects.create(
        user=admin_user,
        position="Administrator"
    )
    print(f"Teacher created: {teacher.user.username}")

# Get or create a center
try:
    center = Center.objects.get(name="Sunshine Childcare Center")
    print(f"Center found: {center.name}")
except Center.DoesNotExist:
    print("Center not found!")
    exit()

# Assign the center to the teacher
if not teacher.center:
    teacher.center = center
    teacher.save()
    print(f"Assigned center {center.name} to teacher {teacher.user.username}")

# Check children in the center
children = Child.objects.filter(center=center)
print(f"\nChildren in center {center.name}:")
for child in children:
    print(f"- {child.name} (Parent: {child.parent.name})")

print(f"\nTotal children in center: {children.count()}")
