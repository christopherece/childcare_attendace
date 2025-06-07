from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from attendance.models import Child, Room, Teacher
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@login_required
def monitor(request):
    # Get the authenticated user
    user = request.user
    
    logger.debug(f"User: {user.username}")
    
    # Get the teacher profile associated with this user
    try:
        teacher = user.teacher_profile
        logger.debug(f"Teacher found: {teacher}")
        center = teacher.center
        logger.debug(f"Center: {center}")
        rooms = teacher.rooms.all()
        room = rooms.first() if rooms.exists() else None
        logger.debug(f"Room: {room}")
    except (Teacher.DoesNotExist, AttributeError):
        logger.debug("No teacher profile found")
        # If user doesn't have a teacher profile, try to get their center from their profile
        try:
            center = user.profile.center
            logger.debug(f"Center from user profile: {center}")
            room = None
        except AttributeError:
            logger.debug("No user profile found")
            # If no profile exists, show all children from all centers
            center = None
            room = None
            logger.debug("No center or room assigned")

    # Get all children in the user's center
    children = Child.objects.all()
    
    logger.debug(f"All children count: {children.count()}")
    
    if center:
        children = children.filter(center=center)
        logger.debug(f"Filtered by center: {children.count()}")
    
    # Get today's date
    today = timezone.now().date()
    
    # Get all rooms in the center
    rooms = Room.objects.filter(center=center) if center else Room.objects.all()
    
    # Get selected room from request parameters
    selected_room_id = request.GET.get('room')
    if selected_room_id:
        room = rooms.filter(id=selected_room_id).first()
        if room:
            children = children.filter(room=room)
    
    # Get selected status from request parameters
    status = request.GET.get('status')
    
    # Get attendance records for today
    attendance_records = []
    for child in children:
        attendance = child.attendance_set.filter(sign_in__date=today).first()
        if attendance:
            if status == 'present' and not attendance.sign_out:
                attendance_records.append({'child': child, 'attendance': attendance})
            elif status == 'absent' and attendance.sign_out:
                attendance_records.append({'child': child, 'attendance': attendance})
            elif not status:  # Show all if no status filter
                attendance_records.append({'child': child, 'attendance': attendance})
        else:
            if status != 'present':  # Show absent if no attendance record
                attendance_records.append({'child': child, 'attendance': None})
    
    logger.debug(f"Attendance records created: {len(attendance_records)}")
    
    context = {
        'attendance_records': attendance_records,
        'center': center,
        'rooms': rooms,
        'selected_room': room,
        'today': today
    }
    
    return render(request, 'monitor/monitor.html', context)
