from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from attendance.models import Child, Parent, Room, Center, Teacher, Attendance

fake = Faker()

class Command(BaseCommand):
    help = 'Generate fake data for children, parents, and rooms'

    def handle(self, *args, **options):
        # First, let's get or create a center
        center_name = fake.company()[:50]  # Truncate long company names
        center_phone = fake.random_number(digits=10)
        center, _ = Center.objects.get_or_create(
            name=center_name,
            address=fake.address(),
            phone=str(center_phone),
            email=fake.email(),
            capacity=100,
            opening_time='08:30:00'
        )

        # Create some rooms
        rooms = []
        age_ranges = [
            "2-3 years",
            "3-4 years",
            "4-5 years"
        ]
        
        for i, age_range in enumerate(age_ranges):
            room = Room.objects.create(
                name=f"Room {i+1}",
                center=center,
                capacity=20,
                age_range=age_range,
                description=fake.paragraph(nb_sentences=1)
            )
            rooms.append(room)

        # Create a teacher (if not exists)
        try:
            teacher_user = User.objects.get(username='teacher1')
        except User.DoesNotExist:
            teacher_user = User.objects.create_user(
                username='teacher1',
                email='teacher@example.com',
                password='password123',
                first_name='John',
                last_name='Doe'
            )

        try:
            teacher = Teacher.objects.get(user=teacher_user)
            teacher.center = center
            teacher.save()
        except Teacher.DoesNotExist:
            teacher = Teacher.objects.create(
                user=teacher_user,
                center=center
            )
        
        teacher.rooms.set(rooms)  # Assign all rooms to the teacher

        # Generate 20 children with their parents
        for i in range(20):
            # Create parent
            try:
                # Generate shorter phone numbers (10 digits)
                emergency_phone = fake.random_number(digits=10)
                
                # Generate unique email by adding timestamp
                timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
                email = f'parent{i+1}_{timestamp}@example.com'
                
                parent = Parent.objects.create(
                    name=fake.name()[:50],  # Truncate name if too long
                    email=email,
                    phone=str(emergency_phone),
                    address=fake.address()
                )
            except Exception as e:
                print(f"Error creating parent: {e}")
                continue

            # Create child
            try:
                child = Child.objects.create(
                    name=fake.name(),
                    parent=parent,
                    center=center,
                    room=rooms[i % len(rooms)],  # Distribute children among rooms
                    date_of_birth=fake.date_of_birth(minimum_age=2, maximum_age=5),
                    gender=fake.random_element(elements=('Male', 'Female', 'Other')),
                    emergency_contact=fake.name(),
                    emergency_phone=str(emergency_phone),
                    allergies=fake.paragraph(nb_sentences=1) if fake.boolean(chance_of_getting_true=30) else '',
                    medical_conditions=fake.paragraph(nb_sentences=1) if fake.boolean(chance_of_getting_true=30) else '',
                    profile_picture=None  # You can add real images later if needed
                )

                # Create some attendance records
                for day in range(5):  # Last 5 days
                    attendance_date = timezone.now() - timezone.timedelta(days=day)
                    if fake.boolean(chance_of_getting_true=70):  # 70% chance of attendance
                        attendance = Attendance.objects.create(
                            child=child,
                            parent=parent,
                            center=center,
                            sign_in=attendance_date.replace(hour=8, minute=fake.random_int(0, 30), second=0),
                            sign_out=attendance_date.replace(hour=16, minute=fake.random_int(0, 30), second=0),
                            notes=fake.sentence(),
                            late=fake.boolean(chance_of_getting_true=10),  # 10% chance of being late
                            late_reason=fake.sentence() if fake.boolean(chance_of_getting_true=10) else ''
                        )
            except Exception as e:
                print(f"Error creating child or attendance records: {e}")
                continue

        self.stdout.write(self.style.SUCCESS('Successfully generated fake data'))
