import os
import django
from django.utils import timezone
from datetime import timedelta

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Child, Attendance

# Get today's date
today = timezone.now().date()

# Get all children with attendance records today
children = Child.objects.filter(
    attendance__created_at__date=today
).distinct()

print(f"Processing {len(children)} children with attendance records today")

# For each child, keep only the first record (sign-in) and remove any others
for child in children:
    attendances = Attendance.objects.filter(
        child=child,
        created_at__date=today
    ).order_by('timestamp')
    
    # If there are multiple records, keep only the first one
    if len(attendances) > 1:
        print(f"Updating {child.name} to signed in status")
        # Delete all but the first record
        for attendance in attendances[1:]:
            attendance.delete()
    
    # If there are no records, create a new sign-in record
    elif len(attendances) == 0:
        print(f"Creating sign-in record for {child.name}")
        Attendance.objects.create(
            child=child,
            parent=child.parent,
            timestamp=timezone.now()
        )

print("\nAll children are now signed in!")
