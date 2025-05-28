from django.shortcuts import render
from django.db.models import Count, Avg, Sum
from datetime import datetime, timedelta
from attendance.models import Child, Parent, Attendance


def admin_portal(request):
    # Get today's date
    today = datetime.now().date()
    current_time = datetime.now()
    
    # Get all children with their attendance status
    children = Child.objects.all()
    children_data = []
    
    for child in children:
        # Get today's attendance records for this child
        todays_attendance = Attendance.objects.filter(
            child=child,
            created_at__date=today
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
    
    # Total number of children
    total_children = Child.objects.count()
    
    # Total number of parents
    total_parents = Parent.objects.count()
    
    # Today's attendance statistics
    todays_attendance = Attendance.objects.filter(
        created_at__date=today
    )
    
    todays_sign_ins = todays_attendance.count()
    todays_sign_outs = todays_attendance.count()
    
    # Weekly statistics
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    weekly_attendance = Attendance.objects.filter(
        created_at__date__range=(week_start, week_end)
    )
    
    weekly_sign_ins = weekly_attendance.count()
    
    # Monthly statistics
    month_start = today.replace(day=1)
    month_end = today
    
    monthly_attendance = Attendance.objects.filter(
        created_at__date__range=(month_start, month_end)
    )
    
    monthly_sign_ins = monthly_attendance.count()
    
    # Most active children (top 5)
    active_children = Child.objects.annotate(
        attendance_count=Count('attendance__id')
    ).order_by('-attendance_count')[:5]
    
    context = {
        'total_children': total_children,
        'total_parents': total_parents,
        'todays_sign_ins': todays_sign_ins,
        'todays_sign_outs': todays_sign_outs,
        'weekly_sign_ins': weekly_sign_ins,
        'monthly_sign_ins': monthly_sign_ins,
        'active_children': active_children,
        'children_data': children_data,
    }
    
    return render(request, 'reports/admin_portal.html', context)
