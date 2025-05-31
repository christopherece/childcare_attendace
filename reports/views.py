from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg, Sum
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import ExtractHour
from django.http import HttpResponse
import csv
from attendance.models import Child, Parent, Attendance, Center, Teacher


def admin_portal(request):
    # Get today's date using timezone-aware datetime
    today = timezone.now().date()
    current_time = timezone.now()
    
    # Get the teacher's center
    teacher = get_object_or_404(Teacher, user=request.user)
    center = teacher.center
    
    # Get children from this center with their attendance status
    children = Child.objects.filter(center=center).select_related('center')
    children_data = []
    
    for child in children:
        # Get today's attendance records for this child
        todays_attendance = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).order_by('sign_in')
        
        is_signed_in = False
        if todays_attendance.exists():
            last_record = todays_attendance.last()
            is_signed_in = last_record.sign_out is None
        
        children_data.append({
            'child': child,
            'is_signed_in': is_signed_in,
            'attendance_records': todays_attendance,
            'center_name': center.name if center else 'Unknown Center'
        })
    
    # Calculate statistics for this center
    total_children = children.count()
    
    # Get signed in children using the same logic as dashboard
    signed_in_children = []
    for child in children:
        # Get today's attendance records
        records = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).order_by('sign_in')
        
        if records.exists():
            last_record = records.last()
            if not last_record.sign_out:  # If there's no sign_out, they're still signed in
                signed_in_children.append(child)
    
    total_signed_in = len(signed_in_children)
    

    
    # Get attendance records for the last 7 days
    week_ago = timezone.now() - timedelta(days=7)
    weekly_records = Attendance.objects.filter(
        sign_in__gte=week_ago
    ).annotate(
        hour=ExtractHour('sign_in')
    )
    
    # Calculate average attendance per hour
    hourly_stats = weekly_records.values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    context = {
        'children': children_data,
        'total_children': total_children,
        'total_signed_in': total_signed_in,
        'total_signed_out': total_children - total_signed_in,
        'hourly_stats': hourly_stats,
        'current_time': current_time
    }
    
    # Handle CSV export with different time periods
    export_type = request.GET.get('export_type', 'daily')  # Default to daily
    export_csv = request.GET.get('export_csv')
    
    if export_csv:
        # Get the first center's name (assuming there's only one center)
        center = Center.objects.first()
        center_name = center.name if center else 'Unknown Center'
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        
        # Set filename based on export type
        filename = f"attendance_report_{export_type}_{today.strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Get date range based on export type
        if export_type == 'daily':
            start_date = today
            end_date = today
        elif export_type == 'weekly':
            start_date = today - timedelta(days=today.weekday())  # Start of current week (Monday)
            end_date = start_date + timedelta(days=6)  # End of current week (Sunday)
        elif export_type == 'monthly':
            start_date = today.replace(day=1)  # Start of current month
            # End of current month (last day)
            next_month = start_date.replace(day=28) + timedelta(days=4)  # This will never fail
            end_date = next_month - timedelta(days=next_month.day)
        
        # Write header section
        writer.writerow(['', '', '', ''])  # Empty row for spacing
        writer.writerow(['Childcare Attendance Report'])
        writer.writerow(['Center:', center_name])
        writer.writerow(['Report Type:', {'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly'}[export_type]])
        writer.writerow(['Date Range:', f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"])
        writer.writerow(['', '', '', ''])  # Empty row for spacing
        
        # Get all attendance records within the date range
        attendance_records = Attendance.objects.filter(
            sign_in__date__gte=start_date,
            sign_in__date__lte=end_date
        ).order_by('child__name', 'sign_in')
        
        # Get all attendance records within the date range
        attendance_records = Attendance.objects.filter(
            sign_in__date__gte=start_date,
            sign_in__date__lte=end_date
        ).order_by('child__name', 'sign_in')
        
        # Process records by child
        current_child = None
        for record in attendance_records:
            if record.child != current_child:
                current_child = record.child
            
            # Write attendance record in a single row format
            writer.writerow([
                record.child.name,
                record.child.parent.name,
                record.sign_in.strftime('%Y-%m-%d %H:%M:%S'),
                record.sign_out.strftime('%Y-%m-%d %H:%M:%S') if record.sign_out else ''
            ])
        
        return response
    
    # Calculate current attendance stats
    currently_signed_in = children.filter(
        attendance__sign_in__date=today,
        attendance__sign_in__lte=current_time
    ).distinct().count()
    
    # Calculate average daily attendance rate
    thirty_days_ago = today - timedelta(days=30)
    total_attendance_records = Attendance.objects.filter(
        sign_in__date__gte=thirty_days_ago
    ).count()
    total_possible_attendances = children.count() * 30
    average_attendance_rate = (total_attendance_records / total_possible_attendances) * 100 if total_possible_attendances > 0 else 0
    
    # Calculate average sign-in and sign-out times
    today_attendances = Attendance.objects.filter(sign_in__date=today)
    if today_attendances.exists():
        # Get all sign-in times as strings
        sign_in_times = [a.sign_in.time() for a in today_attendances]
        
        # Convert times to minutes since midnight
        minutes_since_midnight = [t.hour * 60 + t.minute for t in sign_in_times]
        
        # Calculate average in minutes
        avg_minutes = sum(minutes_since_midnight) / len(minutes_since_midnight)
        
        # Convert back to time
        avg_sign_in_time = (datetime.min + timedelta(minutes=avg_minutes)).time()
        
        # For sign-out time, only consider times after 12 hours ago
        # Use timezone-aware datetime for comparison
        twelve_hours_ago = current_time - timedelta(hours=12)
        sign_out_times = [a.sign_out.time() for a in today_attendances if a.sign_out and a.sign_out >= twelve_hours_ago]
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
        hour=ExtractHour('sign_in')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count').first()

    # Get active children (those with attendance records in the last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    active_children = Child.objects.filter(
        center=center,
        attendance__sign_in__date__gte=thirty_days_ago
    ).annotate(
        attendance_count=Count('attendance')
    ).order_by('-attendance_count')[:10]  # Show top 10 most active children

    context.update({
        'active_children': active_children,
        'currently_signed_in': currently_signed_in,
        'average_attendance_rate': average_attendance_rate,
        'avg_sign_in_time': avg_sign_in_time,
        'avg_sign_out_time': avg_sign_out_time,
        'peak_hour': peak_hour
    })
    
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
