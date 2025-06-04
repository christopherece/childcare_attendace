import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Teacher, Center
from django.contrib.auth.models import User

# Get the admin user
try:
    admin_user = User.objects.get(username='admsrv')
    print(f"Admin user found: {admin_user.username}")
except User.DoesNotExist:
    print("Admin user not found!")
    exit()

# Get or create the center
try:
    center = Center.objects.get(name="Sunshine Childcare Center")
    print(f"Center found: {center.name}")
except Center.DoesNotExist:
    print("Center not found!")
    exit()

# Get or create the teacher
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

# Assign the center to the teacher
if not teacher.center:
    teacher.center = center
    teacher.save()
    print(f"Assigned center {center.name} to teacher {teacher.user.username}")
else:
    print(f"Teacher already has center: {teacher.center.name}")
