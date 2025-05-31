from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from attendance.models import Teacher, Center
import random

class Command(BaseCommand):
    help = 'Create Teacher profiles for existing staff users'

    def add_arguments(self, parser):
        parser.add_argument('--center', type=int, help='ID of the center to assign teachers to')

    def handle(self, *args, **options):
        # Get all staff users
        staff_users = User.objects.filter(is_staff=True)
        
        # Get the specified center or use a random one if not specified
        center = None
        if options['center']:
            try:
                center = Center.objects.get(id=options['center'])
            except Center.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Center with ID {options["center"]} does not exist'))
                return
        else:
            centers = list(Center.objects.all())
            if not centers:
                self.stdout.write(self.style.ERROR('No centers found in the database'))
                return

        # Create teacher profiles
        for user in staff_users:
            try:
                # If center was not specified, assign to a random center
                if not center:
                    center = random.choice(centers)
                
                Teacher.objects.create(
                    user=user,
                    center=center,
                    position='Teacher'
                )
                
                self.stdout.write(self.style.SUCCESS(f'Created teacher profile for {user.get_full_name()}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating profile for {user.get_full_name()}: {str(e)}'))
