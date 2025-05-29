from django.shortcuts import render
from django.db.models import Count, Avg, Sum
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import ExtractHour
from attendance.models import Child, Parent, Attendance


def admin_portal(request):
    # Get today's date using timezone-aware datetime
    today = timezone.now().date()
    current_time = timezone.now()
    
    # Get all children with their attendance status
    children = Child.objects.all()
    children_data = []
    
    for child in children:
        # Get today's attendance records for this child
        todays_attendance = Attendance.objects.filter(
            child=child,
            timestamp__date=today
        ).order_by('timestamp')
        
        status = "Not Signed In"
        sign_in_time = None
        sign_out_time = None
        
        if todays_attendance.exists():
            # Get the first (sign-in) and last (sign-out) records
            first_record = todays_attendance.first()
            last_record = todays_attendance.last()
            
            sign_in_time = first_record.timestamp
            
            if len(todays_attendance) == 2:
                sign_out_time = last_record.timestamp
                status = "Signed Out"
            else:
                status = "Signed In"
            
            children_data.append({
                'child': child,
                'status': status,
                'sign_in_time': sign_in_time,
                'sign_out_time': sign_out_time,
                'parent': child.parent
            })
    
    # Calculate current attendance stats
    currently_signed_in = children.filter(
        attendance__timestamp__date=today,
        attendance__timestamp__lte=current_time
    ).distinct().count()
    
    # Calculate average daily attendance rate
    thirty_days_ago = today - timedelta(days=30)
    total_attendance_records = Attendance.objects.filter(
        timestamp__date__gte=thirty_days_ago
    ).count()
    total_possible_attendances = children.count() * 30
    average_attendance_rate = (total_attendance_records / total_possible_attendances) * 100 if total_possible_attendances > 0 else 0
    
    # Calculate average sign-in and sign-out times
    today_attendances = Attendance.objects.filter(timestamp__date=today)
    if today_attendances.exists():
        # Get all sign-in times as strings
        sign_in_times = [a.timestamp.time() for a in today_attendances]
        
        # Convert times to minutes since midnight
        minutes_since_midnight = [t.hour * 60 + t.minute for t in sign_in_times]
        
        # Calculate average in minutes
        avg_minutes = sum(minutes_since_midnight) / len(minutes_since_midnight)
        
        # Convert back to time
        avg_sign_in_time = (datetime.min + timedelta(minutes=avg_minutes)).time()
        
        # For sign-out time, only consider times after 12 hours ago
        # Use timezone-aware datetime for comparison
        twelve_hours_ago = current_time - timedelta(hours=12)
        sign_out_times = [a.timestamp.time() for a in today_attendances if a.timestamp >= twelve_hours_ago]
        if sign_out_times:
            minutes_since_midnight = [t.hour * 60 + t.minute for t in sign_out_times]
            avg_minutes = sum(minutes_since_midnight) / len(minutes_since_midnight)
            avg_sign_out_time = (datetime.min + timedelta(minutes=avg_minutes)).time()
        else:
            avg_sign_out_time = None
    else:
        avg_sign_in_time = None
        avg_sign_out_time = None
    
    # Calculate peak attendance hour
    peak_hour = today_attendances.annotate(
        hour=ExtractHour('timestamp')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    # Get most active children (top 5)
    active_children = Child.objects.annotate(
        attendance_count=Count('attendance__id')
    ).order_by('-attendance_count')[:5]
    
    context = {
        'total_children': children.count(),
        'total_parents': Parent.objects.count(),
        'currently_signed_in': currently_signed_in,
        'average_attendance_rate': round(average_attendance_rate, 1),
        'avg_sign_in_time': avg_sign_in_time,
        'avg_sign_out_time': avg_sign_out_time,
        'peak_hour': peak_hour['hour'] if peak_hour else None,
        'active_children': active_children,
        'children_data': children_data,
    }
    
    return render(request, 'reports/admin_portal.html', context)
