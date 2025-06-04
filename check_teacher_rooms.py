import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'childcare.settings')
django.setup()

from attendance.models import Teacher, Room, Child

def check_teacher_rooms():
    # Get the teacher named Chris
    try:
        teacher = Teacher.objects.get(user__username='Chris')
        print(f"\nTeacher: {teacher.user.username}")
        print(f"Center: {teacher.center.name}")
        
        # Get all rooms assigned to this teacher
        teacher_rooms = teacher.rooms.all()
        print(f"\nRooms assigned to teacher ({teacher_rooms.count()}):")
        for room in teacher_rooms:
            print(f"- {room.name} (Age Range: {room.age_range})")
            
            # Get children in this room
            children = Child.objects.filter(center=teacher.center, room=room)
            print(f"  Children ({children.count()}):")
            for child in children:
                print(f"    - {child.name} (Parent: {child.parent.name})")
        
        # Get all children in the center
        print(f"\nAll children in center ({teacher.center.name}):")
        center_children = Child.objects.filter(center=teacher.center)
        for child in center_children:
            print(f"- {child.name} (Room: {child.room.name if child.room else 'None'})")
            
    except Teacher.DoesNotExist:
        print("Teacher Chris not found")

if __name__ == '__main__':
    check_teacher_rooms()
