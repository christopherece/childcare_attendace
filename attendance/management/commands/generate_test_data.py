import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from attendance.models import Child, Parent
import names
from random import randint

class Command(BaseCommand):
    help = 'Generate test data for children and parents'

    def handle(self, *args, **options):
        # Generate 30 parent-child pairs
        parents = []
        for i in range(30):
            # Generate random parent
            parent_name = f"{names.get_full_name()}"
            parent_email = f"parent{i}@example.com"
            parent_phone = f"04{randint(10000000, 99999999)}"
            
            parent = Parent.objects.create(
                name=parent_name,
                email=parent_email,
                phone=parent_phone
            )
            parents.append(parent)
            
            # Generate random child for this parent
            child_name = f"{names.get_full_name()}"
            child_gender = random.choice(['Male', 'Female', 'Other'])
            
            # Generate random date of birth (between 1 and 6 years old)
            days_old = random.randint(365, 2190)  # 1-6 years
            dob = timezone.now().date() - timedelta(days=days_old)
            
            # Generate random emergency contact
            emergency_contact = f"{names.get_full_name()}"
            emergency_phone = f"04{randint(10000000, 99999999)}"
            
            # Generate random allergies (20% chance of having allergies)
            has_allergies = random.random() < 0.2
            allergies = random.choice(['Nuts', 'Dairy', 'Eggs', 'Gluten', 'None']) if has_allergies else ''
            
            # Generate random medical conditions (15% chance of having conditions)
            has_conditions = random.random() < 0.15
            medical_conditions = random.choice(['Asthma', 'Diabetes', 'Epilepsy', 'None']) if has_conditions else ''
            
            Child.objects.create(
                name=child_name,
                parent=parent,
                date_of_birth=dob,
                gender=child_gender,
                allergies=allergies,
                medical_conditions=medical_conditions,
                emergency_contact=emergency_contact,
                emergency_phone=emergency_phone
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created {child_name} with parent {parent_name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created 30 test children and parents')
        )
