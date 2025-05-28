import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Child, Attendance
from django.utils import timezone

# Get James Hernandez's child record
child = Child.objects.get(name="James Hernandez")

# Get today's attendance records
attendances = Attendance.objects.filter(
    child=child,
    created_at__date=timezone.now().date()
).order_by('timestamp')

print(f"Number of attendance records for James Hernandez today: {len(attendances)}")
print("\nAttendance records:")
for attendance in attendances:
    print(f"Timestamp: {attendance.timestamp}, Created at: {attendance.created_at}")
