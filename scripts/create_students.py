import random
from datetime import date, timedelta
from faker import Faker
from django.core.management.base import BaseCommand
from attendance.models import Child, Parent, Center, Room

fake = Faker()

class Command(BaseCommand):
    help = 'Create 30 realistic student records'

    def handle(self, *args, **options):
        # Create a center if it doesn't exist
        try:
            center = Center.objects.get(name='FunTime Childcare Center')
        except Center.DoesNotExist:
            center = Center.objects.create(
                name='FunTime Childcare Center',
                address='123 Childcare Street, Wellington',
                phone='04 555 1234',
                email='info@funtimechildcare.nz',
                capacity=50,
                opening_time='08:30:00'
            )

        # Create rooms if they don't exist
        rooms = []
        for name in ['Toddlers Room', 'Preschool Room', 'Kindergarten Room']:
            try:
                room = Room.objects.get(name=name, center=center)
            except Room.DoesNotExist:
                room = Room.objects.create(
                    name=name,
                    center=center,
                    capacity=20,
                    age_range='2-3 years' if name == 'Toddlers Room' else '3-4 years' if name == 'Preschool Room' else '4-5 years',
                    description=f'A safe and nurturing environment for {name}'
                )
            rooms.append(room)

        # Create 30 children with realistic data
        for i in range(30):
            # Generate child data
            child_name = fake.name()
            gender = random.choice(['Male', 'Female', 'Other'])
            
            # Generate realistic DOB (ages 2-5)
            age = random.randint(2, 5)
            dob = date.today() - timedelta(days=random.randint(age*365, (age+1)*365))
            
            # Create parent
            parent_name = fake.name()
            parent_email = f'{parent_name.lower().replace(" ", "")}@example.com'
            try:
                parent = Parent.objects.get(email=parent_email)
            except Parent.DoesNotExist:
                parent = Parent.objects.create(
                    name=parent_name,
                    email=parent_email,
                    phone=fake.phone_number()
                )
            
            # Create child
            child = Child.objects.create(
                name=child_name,
                parent=parent,
                center=center,
                room=random.choice(rooms),
                date_of_birth=dob,
                gender=gender,
                emergency_contact=parent_name,
                emergency_phone=fake.phone_number(),
                allergies=fake.sentence() if random.random() < 0.2 else '',  # 20% chance of having allergies
                medical_conditions=fake.sentence() if random.random() < 0.1 else ''  # 10% chance of having medical conditions
            )
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created child: {child_name}'))

        self.stdout.write(self.style.SUCCESS('Successfully created 30 children with realistic data'))
