from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import ExtractHour
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv
from django.contrib import messages
from django.db import transaction
from attendance.models import Child, Parent, Attendance, Center, Teacher, Room

# Add new view for child details
def child_details(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    parent = child.parent
    
    # Handle form submission
    if request.method == 'POST':
        # Update child information
        child.name = request.POST.get('child_name', child.name)
        child.gender = request.POST.get('gender', child.gender)
        child.allergies = request.POST.get('allergies', child.allergies)
        child.medical_conditions = request.POST.get('medical_conditions', child.medical_conditions)
        child.emergency_contact = request.POST.get('emergency_contact', child.emergency_contact)
        child.emergency_phone = request.POST.get('emergency_phone', child.emergency_phone)
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            child.profile_picture = request.FILES['profile_picture']
        
        # Update parent information
        parent.name = request.POST.get('parent_name', parent.name)
        parent.email = request.POST.get('parent_email', parent.email)
        parent.phone = request.POST.get('parent_phone', parent.phone)
        parent.address = request.POST.get('parent_address', parent.address)
        
        try:
            with transaction.atomic():
                child.save()
                parent.save()
                messages.success(request, 'Child information updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating information: {str(e)}')
            
    # Get recent attendance records
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_attendance = Attendance.objects.filter(
        child=child,
        sign_in__date__gte=thirty_days_ago
    ).order_by('-sign_in')
    
    # Calculate attendance statistics
    total_possible_days = (timezone.now().date() - thirty_days_ago).days + 1
    total_attended_days = recent_attendance.count()
    attendance_rate = (total_attended_days / total_possible_days * 100) if total_possible_days > 0 else 0
    
    # Prepare medical information
    medical_info = {
        'allergies': child.allergies if child.allergies else '',
        'medical_conditions': child.medical_conditions if child.medical_conditions else '',
        'emergency_contact': child.emergency_contact,
        'emergency_phone': child.emergency_phone
    }
    
    # Get the correct profile picture URL
    if child.profile_picture:
        profile_picture_url = child.profile_picture.url
    else:
        profile_picture_url = '/static/images/child_pix/user-default.png'
    
    context = {
        'child': child,
        'parent': parent,
        'recent_attendance': recent_attendance,
        'attendance_rate': f'{attendance_rate:.1f}%',
        'medical_info': medical_info,
        'profile_picture_url': profile_picture_url,
        'genders': ['Male', 'Female', 'Other']
    }
    return render(request, 'reports/child_details.html', context)


def admin_portal(request):
    # Get today's date using timezone-aware datetime
    today = timezone.now().date()
    current_time = timezone.now()
    
    # Get the teacher's center and rooms
    try:
        teacher = get_object_or_404(Teacher, user=request.user)
        center = teacher.center
        
        if not center:
            messages.error(request, 'You are not assigned to any center')
            return redirect('attendance:dashboard')
    except Teacher.DoesNotExist:
        messages.error(request, 'You are not a teacher')
        return redirect('attendance:dashboard')
    
    # Get all rooms assigned to this teacher
    teacher_rooms = teacher.rooms.all()
    print(f"\nTeacher rooms: {teacher_rooms.count()}")
    for room in teacher_rooms:
        print(f"- {room.name} (Age Range: {room.age_range})")
    
    # Get all children in this center
    all_center_children = Child.objects.filter(center=center).select_related('center', 'parent', 'room')
    print(f"\nAll center children: {all_center_children.count()}")
    for child in all_center_children:
        print(f"- {child.name} (Room: {child.room.name if child.room else 'None'})")
    
    # Get children from this center with their attendance status, sorted alphabetically
    # Match children by their room's age range instead of exact room name
    children = Child.objects.filter(
        center=center,
        room__age_range__in=[room.age_range for room in teacher_rooms]
    ).select_related('center', 'parent', 'room').order_by('name')
    
    print(f"\nFiltered children: {children.count()}")
    for child in children:
        print(f"- {child.name} (Room: {child.room.name if child.room else 'None'})")
    
    print(f"\nTotal children before filters: {children.count()}")
    for child in children:
        print(f"- {child.name} (Room: {child.room.name if child.room else 'None'})")
    
    # Apply filters if present
    status_filter = request.GET.get('status', '')
    room_filter = request.GET.get('room', '')
    
    # Filter by room if specified
    if room_filter:
        children = children.filter(room__name=room_filter)
        print(f"\nAfter room filter (room='{room_filter}'):")
        print(f"Total children: {children.count()}")
        for child in children:
            print(f"- {child.name} (Room: {child.room.name if child.room else 'None'})")
    
    if status_filter:
        if status_filter == 'signed_in':
            children = children.filter(attendance__sign_in__date=today, attendance__sign_out__isnull=True)
        elif status_filter == 'signed_out':
            children = children.filter(attendance__sign_in__date=today, attendance__sign_out__isnull=False)
        elif status_filter == 'not_signed':
            children = children
        print(f"\nAfter status filter (status='{status_filter}'):")
        print(f"Total children: {children.count()}")
        for child in children:
            print(f"- {child.name} (Room: {child.room.name if child.room else 'None'})")
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        children = children.filter(
            Q(name__icontains=search_query) |
            Q(parent__name__icontains=search_query)
        )
        print(f"\nAfter search filter (search='{search_query}'):")
        print(f"Total children: {children.count()}")
        for child in children:
            print(f"- {child.name} (Parent: {child.parent.name}, Room: {child.room.name if child.room else 'None'})")
    
    # First get all attendance statistics before pagination
    all_children_data = []
    thirty_days_ago = today - timedelta(days=30)
    
    # Get attendance statistics for each child
    for child in children:
        print(f"\nProcessing child: {child.name} (Room: {child.room.name if child.room else 'None'})")
        
        # Get today's attendance records for this child
        todays_attendance = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).order_by('sign_in')
        
        # Get attendance records for the last 30 days
        recent_attendance = Attendance.objects.filter(
            child=child,
            sign_in__date__gte=thirty_days_ago
        )
        
        # Calculate attendance rate for this child
        total_possible_days = (today - thirty_days_ago).days + 1
        total_attended_days = recent_attendance.count()
        attendance_rate = (total_attended_days / total_possible_days * 100) if total_possible_days > 0 else 0
        
        # Check current attendance status
        is_signed_in = False
        has_attendance = False
        current_attendance_time = None
        
        if todays_attendance.exists():
            has_attendance = True
            last_record = todays_attendance.last()
            is_signed_in = last_record.sign_out is None
            if is_signed_in:
                current_attendance_time = last_record.sign_in.time().strftime('%H:%M')
        
        all_children_data.append({
            'child': child,
            'is_signed_in': is_signed_in,
            'has_attendance': has_attendance,
            'attendance_records': todays_attendance,
            'attendance_rate': f'{attendance_rate:.1f}%',
            'child_id': child.id
        })
    
    # Sort all children by attendance rate
    all_children_data = sorted(all_children_data, key=lambda x: float(x['attendance_rate'].rstrip('%')), reverse=True)
    
    # Now apply pagination
    paginator = Paginator(all_children_data, 10)  # 10 children per page
    page = request.GET.get('page', 1)
    try:
        children_data = paginator.page(page)
    except PageNotAnInteger:
        children_data = paginator.page(1)
    except EmptyPage:
        children_data = paginator.page(paginator.num_pages)
    
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
    
    # Add most active children section
    # Get all children's attendance rates
    children_attendance_rates = []
    for child_data in all_children_data:
        children_attendance_rates.append({
            'child': child_data['child'],
            'attendance_rate': float(child_data['attendance_rate'].rstrip('%'))
        })
    
    # Sort by attendance rate and get top 5
    most_active_children = sorted(
        children_attendance_rates,
        key=lambda x: x['attendance_rate'],
        reverse=True
    )[:5]
    
    # Debugging - print out some information
    print(f"Total children: {len(children)}")
    print(f"Signed in children: {total_signed_in}")
    print(f"Children attendance rates: {children_attendance_rates}")
    
    # Debugging - print out most active children
    print("\nMost active children:")
    for child in most_active_children:
        print(f"- {child['child'].name}: {child['attendance_rate']}% attendance")
    
    # Calculate statistics for this center
    total_children = len(children)
    
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
        'total_children': children.count(),
        'total_signed_in': sum(1 for child_data in all_children_data if child_data['is_signed_in']),
        'total_signed_out': children.count() - sum(1 for child_data in all_children_data if child_data['is_signed_in']),
        'hourly_stats': hourly_stats,
        'current_time': current_time,
        'most_active_children': most_active_children,
        'center': center,
        'teacher_rooms': teacher_rooms
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
        writer.writerow(['Childcare Attendance Report', '', '', ''])
        writer.writerow(['Center:', center_name, '', ''])
        writer.writerow(['Report Type:', {'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly'}[export_type], '', ''])
        writer.writerow(['Date Range:', f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}", '', ''])
        writer.writerow(['', '', '', ''])  # Empty row for spacing
        
        # Get teacher's profile
        teacher = request.user.teacher_profile
        
        # Get all children from teacher's center and rooms
        children = Child.objects.filter(
            center=teacher.center,
            room__in=teacher.rooms.all()
        ).order_by('name')
        
        # For each child, get their attendance records within the date range
        for child in children:
            # Get child's attendance records
            attendance_records = Attendance.objects.filter(
                child=child,
                sign_in__date__gte=start_date,
                sign_in__date__lte=end_date
            ).order_by('sign_in')
            
            # Write child header row
            writer.writerow([
                child.name,
                child.parent.name,
                child.room.name if child.room else '',
                '',
                '',
                ''
            ])
            
            # If there are attendance records, write them
            if attendance_records.exists():
                for record in attendance_records:
                    writer.writerow([
                        '',
                        '',
                        record.sign_in.strftime('%d/%m/%Y %H:%M'),
                        record.sign_out.strftime('%d/%m/%Y %H:%M') if record.sign_out else 'Not signed out',
                        'Late' if record.late else 'On Time',
                        record.notes or ''
                    ])
            else:
                # If no attendance records, show "No attendance today"
                writer.writerow([
                    '',
                    '',
                    'No attendance today',
                    '',
                    '',
                    ''
                ])
        
        # Write column headers
        writer.writerow(['Child Name', 'Parent Name', 'Sign In Time', 'Sign Out Time', 'Status', 'Notes'])
        
        # Process records by child
        current_child = None
        for record in attendance_records:
            if record.child != current_child:
                current_child = record.child
                # Write child header row
                writer.writerow([
                    record.child.name,
                    record.child.parent.name,
                    record.sign_in.strftime('%d/%m/%Y %H:%M'),
                    record.sign_out.strftime('%d/%m/%Y %H:%M') if record.sign_out else 'Not signed out',
                    'Late' if record.late else 'On Time',
                    record.notes or ''
                ])
            else:
                # Write additional attendance record
                writer.writerow([
                    '',
                    '',
                    record.sign_in.strftime('%d/%m/%Y %H:%M'),
                    record.sign_out.strftime('%d/%m/%Y %H:%M') if record.sign_out else 'Not signed out',
                    'Late' if record.late else 'On Time',
                    record.notes or ''
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
