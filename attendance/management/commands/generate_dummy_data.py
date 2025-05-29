from django.core.management.base import BaseCommand
from django.utils import timezone
import random
from faker import Faker
from attendance.models import Center, Parent, Child, Attendance

class Command(BaseCommand):
    help = 'Generate dummy data for centers, parents, and children'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force delete existing data before generating new data')

fake = Faker()

class Command(BaseCommand):
    help = 'Generate dummy data for centers, parents, and children'

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # If force flag is set, delete existing data
        if force:
            self.stdout.write(self.style.WARNING('Deleting existing data...'))
            Center.objects.all().delete()
            Parent.objects.all().delete()
            Child.objects.all().delete()
            Attendance.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data deleted'))
        # Create 4 specific centers
        centers = []
        center_names = [
            'Best Childcare Beach Haven',
            'Best Childcare Glenfield',
            'Best Childcare Northcote',
            'Best Childcare Takapuna'
        ]
        
        for name in center_names:
            # Generate unique email suffix
            suffix = random.randint(1000, 9999)
            center = Center.objects.create(
                name=name,
                address=fake.address(),
                phone=f'+64 {random.randint(9, 99)} {random.randint(1000000, 9999999)}',
                email=f"{name.lower().replace(' ', '_')}{suffix}@bestchildcare.co.nz",
                capacity=random.randint(50, 100)
            )
            centers.append(center)
            self.stdout.write(self.style.SUCCESS(f'Created center: {center.name}'))

        # Create parents and children
        for i in range(30):
            # Create a parent
            parent = Parent.objects.create(
                name=fake.name(),
                email=fake.email(),
                phone=f'+64 {random.randint(9, 99)} {random.randint(1000000, 9999999)}',
                address=fake.address()
            )

            # Create a child
            days_ago = random.randint(730, 1825)  # 2-5 years
            birth_date = timezone.now() - timezone.timedelta(days=days_ago)
            
            # Randomly select gender
            gender = random.choice(['Male', 'Female', 'Other'])
            
            # Randomly select a center
            center = random.choice(centers)
            
            child = Child.objects.create(
                name=fake.name(),
                parent=parent,
                center=center,
                date_of_birth=birth_date.date(),
                gender=gender,
                allergies=", ".join(random.sample(['Peanuts', 'Shellfish', 'Dairy', 'Eggs', 'Soy', 'Wheat'], random.randint(0, 3))) if random.random() < 0.3 else None,
                medical_conditions=", ".join(random.sample(['Asthma', 'Eczema', 'Diabetes', 'Seizure disorder', 'Food allergies'], random.randint(0, 2))) if random.random() < 0.2 else None,
                emergency_contact=fake.name(),
                emergency_phone=f'+64 {random.randint(9, 99)} {random.randint(1000000, 9999999)}'
            )

            self.stdout.write(self.style.SUCCESS(f'Created child: {child.name} at {center.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully created dummy data'))
