import os
import django
from django.utils import timezone
from datetime import timedelta

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Child, Attendance
from django.db import models

# Get all children with more than 2 attendance records today
duplicate_children = Child.objects.filter(
    attendance__created_at__date=timezone.now().date()
).annotate(
    record_count=models.Count('attendance__id')
).filter(
    record_count__gt=2
)

print(f"Found {len(duplicate_children)} children with duplicate records today")

# For each child, keep only the first two records and delete the rest
for child in duplicate_children:
    attendances = Attendance.objects.filter(
        child=child,
        created_at__date=timezone.now().date()
    ).order_by('timestamp')
    
    # Keep only the first two records
    if len(attendances) > 2:
        print(f"Fixing duplicates for {child.name}")
        for attendance in attendances[2:]:
            attendance.delete()

print("\nDuplicate records have been fixed!")
