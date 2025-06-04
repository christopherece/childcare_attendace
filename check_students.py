import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Child, Parent, Center, Room, Teacher

def check_students():
    print("Checking students in database...")
    
    # Get all centers
    centers = Center.objects.all()
    print(f"\nTotal centers: {centers.count()}")
    
    # Get all teachers
    teachers = Teacher.objects.all()
    print(f"\nTotal teachers: {teachers.count()}")
    for teacher in teachers:
        print(f"\nTeacher: {teacher.user.username}")
        print(f"Center: {teacher.center.name}")
        
        # Get rooms assigned to this teacher
        teacher_rooms = teacher.rooms.all()
        print(f"Rooms assigned to teacher ({teacher_rooms.count()}):")
        for room in teacher_rooms:
            print(f"  - {room.name} ({room.age_range})")
            
            # Get children in this room
            children = Child.objects.filter(center=teacher.center, room=room)
            print(f"    Children ({children.count()}):")
            for child in children:
                print(f"      - {child.name} (Parent: {child.parent.name})")
    
    # Get children without rooms
    children_without_rooms = Child.objects.filter(center__isnull=False, room__isnull=True)
    print(f"\nChildren without rooms ({children_without_rooms.count()}):")
    for child in children_without_rooms:
        print(f"  - {child.name} (Parent: {child.parent.name})")

if __name__ == '__main__':
    check_students()
