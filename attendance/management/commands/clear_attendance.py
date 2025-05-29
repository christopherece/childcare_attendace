from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from attendance.models import Attendance

class Command(BaseCommand):
    help = 'Clear attendance records from previous days'

    def handle(self, *args, **options):
        today = timezone.now().date()
        deleted_count, _ = Attendance.objects.filter(
            timestamp__date__lt=today
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleared {deleted_count} attendance records from previous days')
        )
