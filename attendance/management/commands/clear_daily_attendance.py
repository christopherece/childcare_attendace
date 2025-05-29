from django.core.management.base import BaseCommand
from django.utils import timezone
from attendance.models import Attendance
from datetime import timedelta

class Command(BaseCommand):
    help = 'Clear attendance records from the previous day'

    def handle(self, *args, **options):
        # Get yesterday's date
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Delete all attendance records from yesterday
        deleted_count, _ = Attendance.objects.filter(
            timestamp__date=yesterday
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleared {deleted_count} attendance records from {yesterday}')
        )
