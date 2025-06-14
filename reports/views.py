from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import ExtractHour
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.db import transaction
from attendance.models import Child, Parent, Attendance, Center, Teacher, Room
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.template.loader import render_to_string
from django.db.models import Prefetch

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


from .pdf_generator import generate_attendance_pdf

def generate_pdf_report(attendances, report_type, request):
    """Generate PDF report with professional layout"""
    try:
        # Get selected date and room from request
        selected_date = request.GET.get('date')
        selected_room_id = request.GET.get('room')
        
        # Get center name from request session or default
        center_name = request.session.get('center_name', 'Childcare Center')
        
        # Get room name if selected
        room_name = ''
        if selected_room_id:
            try:
                room = Room.objects.get(id=selected_room_id)
                room_name = room.name
                # Filter attendances by room
                attendances = attendances.filter(child__room_id=selected_room_id)
            except Room.DoesNotExist:
                return HttpResponseBadRequest("Selected room not found")
            
        # If no room selected, use "All Rooms"
        if not selected_room_id:
            room_name = "All Rooms"
            
        # Validate date format if provided
        if selected_date:
            try:
                datetime.strptime(selected_date, '%Y-%m-%d')
            except ValueError:
                return HttpResponseBadRequest("Invalid date format. Please use YYYY-MM-DD")
        
        # Generate PDF using the new generator
        try:
            pdf = generate_attendance_pdf(attendances, selected_date, room_name, center_name)
            return pdf
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return HttpResponseBadRequest(f"Error generating PDF: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return HttpResponseBadRequest("An unexpected error occurred while generating the PDF")


def child_attendance_report(request, child_id):
    """Generate a detailed attendance report for a specific child"""
    try:
        child = get_object_or_404(Child, id=child_id)
        
        # Get date range from query parameters or use last 30 days
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)

        # Get attendance records for the date range
        attendances = Attendance.objects.filter(
            child=child,
            sign_in__date__range=(start_date, end_date)
        ).order_by('sign_in')

        # Calculate statistics
        total_days = (end_date - start_date).days + 1
        total_attended_days = attendances.count()
        attendance_rate = (total_attended_days / total_days * 100) if total_days > 0 else 0

        # Calculate average times
        avg_sign_in_time = attendances.aggregate(avg_sign_in=Avg('sign_in'))['avg_sign_in']
        avg_sign_out_time = attendances.aggregate(avg_sign_out=Avg('sign_out'))['avg_sign_out']

        # Format average times
        avg_sign_in_time = avg_sign_in_time.strftime('%I:%M %p') if avg_sign_in_time else '-'
        avg_sign_out_time = avg_sign_out_time.strftime('%I:%M %p') if avg_sign_out_time else '-'

        context = {
            'child': child,
            'attendances': attendances,
            'total_attended_days': total_attended_days,
            'attendance_rate': f'{attendance_rate:.1f}',
            'avg_sign_in_time': avg_sign_in_time,
            'avg_sign_out_time': avg_sign_out_time,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'current_date': timezone.now().strftime('%Y-%m-%d'),
            'current_year': timezone.now().year
        }

        return render(request, 'reports/child_attendance_report.html', context)

    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('reports:admin_portal')


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_portal(request):
    """Admin portal view for managing attendance reports"""
    # Check if user is authenticated and has teacher profile
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to access this page")
        return redirect('login')
    
    try:
        teacher = get_object_or_404(Teacher, user=request.user)
        center = teacher.center
        center_name = center.name if center else "No Center"
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found")
        return redirect('attendance:dashboard')
    
    # Get today's date using timezone-aware datetime
    current_time = timezone.now()
    
    # Get date from URL parameter or use today
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Check if we should show the attendance report view
    view_type = request.GET.get('view')
    if view_type == 'attendance_report':
        # Get child ID from query parameters
        child_id = request.GET.get('child_id')
        if child_id:
            return child_attendance_report(request, child_id)
        else:
            messages.error(request, 'No child selected for attendance report')
            return redirect('reports:admin_portal')
    
    # Handle PDF export
    if request.GET.get('export_pdf') == '1':
        selected_date = request.GET.get('date')
        selected_room_id = request.GET.get('room')
        
        # Get attendance records for PDF
        pdf_attendances = Attendance.objects.filter(
            child__center=center,
            sign_in__date=selected_date
        ).select_related('child')
        
        if selected_room_id:
            pdf_attendances = pdf_attendances.filter(child__room_id=selected_room_id)
            
        # Get room name if selected
        room_name = "All Rooms"
        if selected_room_id:
            try:
                room = Room.objects.get(id=selected_room_id)
                room_name = room.name
            except Room.DoesNotExist:
                pass
        
        # Get all children in the room
        children = Child.objects.filter(room__center=center)
        if selected_room_id:
            children = children.filter(room_id=selected_room_id)
        
        # Format attendance data for PDF - include all children
        pdf_data = []
        for child in children:
            # Get attendance record for this child
            attendance = pdf_attendances.filter(child=child).first()
            
            pdf_data.append({
                'child': {
                    'name': child.name,
                    'id': child.id,
                    'parent': {
                        'name': child.parent.name if child.parent else None
                    }
                },
                'sign_in_time': attendance.sign_in.strftime('%I:%M %p') if attendance else '-',
                'sign_out_time': attendance.sign_out.strftime('%I:%M %p') if attendance and attendance.sign_out else '-',
                'status': 'Present' if attendance and attendance.sign_out is None else 'Absent',
                'notes': attendance.notes if attendance and attendance.notes else ''
            })
        
        # Generate PDF
        return generate_attendance_pdf(pdf_data, selected_date, room_name, center_name)
    
    # Get room data and attendance statistics
    rooms = Room.objects.filter(center=center).prefetch_related(
        'children',
        'children__attendance_set'
    )
    
    # Calculate attendance statistics for each room
    room_stats = []
    current_time = timezone.now()
    
    # Get today's date using timezone-aware datetime
    today = timezone.now().date()
    
    for room in rooms:
        # Get all children in this room
        children = Child.objects.filter(room=room)
        total_children = children.count()
        
        # Count signed in children and build attendance list
        signed_in_children = 0
        room_attendance = []
        
        # Get all children in this room
        children = Child.objects.filter(room=room).select_related('parent')
        total_children = children.count()
        
        for child in children:
            # Get today's attendance for this child
            attendance = Attendance.objects.filter(
                child=child,
                sign_in__date=today
            ).first()
            
            if attendance:
                signed_in_children += 1
                status = 'Present'
                sign_in_time = attendance.sign_in.strftime('%I:%M %p')
            else:
                status = 'Absent'
                sign_in_time = '-'  # Show dash for absent children
            
            room_attendance.append({
                'child': child,
                'status': status,
                'sign_in_time': sign_in_time,
                'parent': child.parent.name if child.parent else 'No Parent'
            })
        
        # Calculate attendance percentage
        attendance_percentage = (signed_in_children / total_children * 100) if total_children > 0 else 0
        
        # Add room stats to list
        room_stats.append({
            'room': room,
            'total_children': total_children,
            'signed_in_children': signed_in_children,
            'attendance_percentage': attendance_percentage,
            'attendance': room_attendance
        })
    
    # Calculate overall statistics
    total_children = sum(stat['total_children'] for stat in room_stats)
    total_signed_in = sum(stat['signed_in_children'] for stat in room_stats)
    
    # Get attendance records for display (separate from PDF data)
    display_attendances = []
    
    # Get selected date and room from query parameters
    selected_date_str = request.GET.get('date')
    selected_room_id = request.GET.get('room')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else today
    except (ValueError, TypeError):
        selected_date = today
    
    # Get attendance records for display
    attendance_records = Attendance.objects.filter(
        child__center=center,
        sign_in__date=selected_date
    ).select_related('child')
    
    # Apply room filter if selected
    if selected_room_id:
        attendance_records = attendance_records.filter(child__room_id=selected_room_id)
    
    # Format attendance data for display
    for attendance in attendance_records:
        display_attendances.append({
            'child': attendance.child,
            'status': 'Present',
            'sign_in_time': attendance.sign_in.strftime('%I:%M %p'),
            'sign_out_time': attendance.sign_out.strftime('%I:%M %p') if attendance.sign_out else '-'
        })
    
    # Calculate average attendance time
    avg_attendance_time = None
    if attendance_records.exists():
        total_time = timedelta()
        for attendance in attendance_records:
            if attendance.sign_out:
                total_time += attendance.sign_out - attendance.sign_in
        avg_attendance_time = total_time / attendance_records.count()
    
    # Calculate peak attendance hour
    peak_hour = None
    if attendance_records.exists():
        hour_counts = attendance_records.annotate(
            hour=ExtractHour('sign_in')
        ).values('hour').annotate(count=Count('id')).order_by('-count')
        if hour_counts:
            peak_hour = hour_counts.first()['hour']
    currently_signed_in = sum(stat['signed_in_children'] for stat in room_stats)
    overall_attendance_percentage = (currently_signed_in / total_children * 100) if total_children > 0 else 0
    
    # Get selected room from query parameters
    selected_room = request.GET.get('room')
    
    # Get all children from the center
    children = Child.objects.filter(center=center)
    
    # Filter by room if specified
    if selected_room:
        children = children.filter(room_id=selected_room)
    
    # Get all attendance records for the selected date
    attendance_records = Attendance.objects.filter(
        sign_in__date=selected_date
    ).select_related('child', 'child__parent', 'child__room')
    
    # If room is selected, filter attendance records
    if selected_room:
        attendance_records = attendance_records.filter(child__room_id=selected_room)
    
    # Handle PDF export if requested
    if request.GET.get('export_pdf') == '1':
        return generate_pdf_report(attendance_records, 'daily', request)
    
    # Calculate attendance statistics
    total_children = children.count()
    signed_in_children = attendance_records.count()
    overall_attendance_percentage = (signed_in_children / total_children * 100) if total_children > 0 else 0
    
    # Get display data - include all children from the room, even those without attendance
    display_attendances = []
    for child in children:
        # Get attendance record for this child
        attendance = attendance_records.filter(child=child).first()
        
        # Create display data with default values
        attendance_data = {
            'child': child,
            'status': 'Present' if attendance else 'Absent',
            'sign_in_time': attendance.sign_in.strftime('%I:%M %p') if attendance and attendance.sign_in else '-',
            'sign_out_time': attendance.sign_out.strftime('%I:%M %p') if attendance and attendance.sign_out else '-',
            'notes': attendance.notes if attendance else ''
        }
        display_attendances.append(attendance_data)
    
    # Sort by child name
    display_attendances.sort(key=lambda x: x['child'].name)
    
    # Calculate attendance by time
    attendance_by_time = []
    for attendance in display_attendances:
        if attendance['status'] == 'Present' and attendance['sign_in_time']:
            hour = datetime.strptime(attendance['sign_in_time'], '%I:%M %p').hour
            attendance_by_time.append({'hour': hour})
    
    # Calculate attendance types
    attendance_types = ['Present', 'Absent']
    attendance_counts = [
        len([a for a in display_attendances if a['status'] == 'Present']),
        len([a for a in display_attendances if a['status'] == 'Absent'])
    ]
    
    # Get active children
    active_children = []
    for attendance in display_attendances:
        if attendance['status'] == 'Present':
            active_children.append(attendance['child'])
    
    # Calculate average attendance rate
    if active_children:
        total_attendance = len([a for a in display_attendances if a['status'] == 'Present'])
        average_attendance_rate = (total_attendance / len(display_attendances) * 100) if len(display_attendances) > 0 else 0
    else:
        average_attendance_rate = 0
    
    # Get attendance data for chart
    attendance_data = []
    for attendance in display_attendances:
        attendance_data.append({
            'name': attendance['child'].name,
            'attendance': 1 if attendance['status'] == 'Present' else 0,
            'total_days': 1
        })
    
    # Get rooms with attendance data
    rooms_with_data = []
    if selected_room:
        room = Room.objects.get(id=selected_room)
        rooms_with_data.append({
            'room': room,
            'total_children': len(display_attendances),
            'present': len([a for a in display_attendances if a['status'] == 'Present']),
            'absent': len([a for a in display_attendances if a['status'] == 'Absent'])
        })
    else:
        for room in rooms:
            room_children = children.filter(room=room)
            room_attendance = attendance_records.filter(child__in=room_children)
            rooms_with_data.append({
                'room': room,
                'total_children': room_children.count(),
                'present': room_attendance.count(),
                'absent': room_children.count() - room_attendance.count()
            })
    total_attendance = 0
    for child in children:
        if Attendance.get_daily_attendance(child, selected_date):
            total_attendance += 1
    average_attendance_rate = (total_attendance / total_children * 100) if total_children > 0 else 0

    # Calculate time-based statistics
    avg_sign_in_time = None
    avg_sign_out_time = None
    total_sign_in_hours = 0
    total_sign_out_hours = 0
    count_sign_in = 0
    count_sign_out = 0
    
    for attendance in display_attendances:
        if attendance['status'] == 'Present':
            try:
                sign_in = datetime.strptime(attendance['sign_in_time'], '%I:%M %p')
                total_sign_in_hours += sign_in.hour
                count_sign_in += 1
            except (ValueError, TypeError):
                pass
            
            try:
                sign_out = datetime.strptime(attendance['sign_out_time'], '%I:%M %p')
                total_sign_out_hours += sign_out.hour
                count_sign_out += 1
            except (ValueError, TypeError):
                pass
    
    if count_sign_in > 0:
        avg_sign_in_time = total_sign_in_hours / count_sign_in
    if count_sign_out > 0:
        avg_sign_out_time = total_sign_out_hours / count_sign_out

    # Get peak attendance hour
    peak_hour = None
    peak_count = 0
    hour_counts = {}
    
    for attendance in display_attendances:
        if attendance['status'] == 'Present' and attendance['sign_in_time']:
            try:
                sign_in = datetime.strptime(attendance['sign_in_time'], '%I:%M %p')
                hour = sign_in.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
                if hour_counts[hour] > peak_count:
                    peak_count = hour_counts[hour]
                    peak_hour = hour
            except (ValueError, TypeError):
                pass

    # Get attendance by time
    attendance_by_time = []
    for hour in range(24):
        count = hour_counts.get(hour, 0)
        attendance_by_time.append({'hour': hour, 'count': count})

    # Get room data and attendance statistics
    rooms = Room.objects.filter(center=center).prefetch_related(
        'children',
        'children__attendance_set'
    )
    
    # Get all attendances for the selected date
    date_attendances = {a.child_id: a for a in Attendance.objects.filter(sign_in__date=selected_date)}
    
    # Debug print to check rooms and children
    print("\nRooms found:")
    for room in rooms:
        print(f"Room: {room.name}")
        print(f"Children count: {room.children.count()}")
        for child in room.children.all():
            attendance_count = child.attendance_set.filter(sign_in__date=selected_date).count()
            print(f"  - {child.name}")
            print(f"    Attendance records: {attendance_count}")
    
    # Prepare data for template
    attendance_data = {}
    rooms_with_data = []
    
    for room in rooms:
        room_children = room.children.all()
        room_data = []
        
        # Calculate attendance statistics for the room
        total_children = room_children.count()
        signed_in_count = sum(1 for child in room_children if date_attendances.get(child.id))
        attendance_rate = (signed_in_count / total_children * 100) if total_children > 0 else 0
        
        # Add attendance statistics to room object
        setattr(room, 'attendance_count', signed_in_count)
        setattr(room, 'attendance_rate', f'{attendance_rate:.1f}')
        
        for child in room_children:
            # Add is_signed_in property
            setattr(child, 'is_signed_in', date_attendances.get(child.id) is not None)
            
            # Add sign_in_time if signed in
            if child.is_signed_in:
                attendance = date_attendances[child.id]
                setattr(child, 'sign_in_time', attendance.sign_in.strftime('%I:%M %p'))
            else:
                setattr(child, 'sign_in_time', None)
            
            child_data = {
                'child': child,
                'records': []
            }
            
            # Get attendance records for this child
            records = Attendance.objects.filter(
                child=child,
                sign_in__date=selected_date
            ).order_by('sign_in')
            
            for record in records:
                status = 'Signed In' if record.sign_out is None else 'Signed Out'
                child_data['records'].append({
                    'sign_in': record.sign_in.strftime('%I:%M %p'),
                    'sign_out': record.sign_out.strftime('%I:%M %p') if record.sign_out else None,
                    'status': status,
                    'notes': record.notes
                })
            
            room_data.append((child, child_data['records']))
        
        attendance_data[room.name] = dict(room_data)
        rooms_with_data.append(room)
    
    # Get attendance status counts
    attendance_types = ['Present', 'Absent']
    attendance_counts = [
        Attendance.objects.filter(
            child__center=center,
            sign_in__date=selected_date
        ).count(),
        Child.objects.filter(center=center).count() - total_attendance
    ]

    # Pass room stats to template
    context = {
        'center_name': center_name,
        'rooms': rooms,
        'room_stats': room_stats,
        'attendance_records': attendance_records,
        'total_children': total_children,
        'signed_in_children': signed_in_children,
        'overall_attendance_percentage': overall_attendance_percentage,
        'avg_attendance_time': avg_attendance_time,
        'peak_hour': peak_hour,
        'selected_date': selected_date,
        'display_attendances': display_attendances,
        'children': children,
        'selected_room': selected_room,
        'date': selected_date,
        'avg_sign_in_time': avg_sign_in_time,
        'avg_sign_out_time': avg_sign_out_time,
        'attendance_by_time': attendance_by_time,
        'average_attendance_rate': average_attendance_rate,
        'attendance_data': attendance_data,
        'rooms_with_data': rooms_with_data,
        'attendance_types': attendance_types,
        'attendance_counts': attendance_counts
    }
    
    return render(request, 'reports/admin_portal.html', context)

    # ... (rest of the code remains the same)

    # Get active children
    active_children = Child.objects.filter(
        center=center,
        attendance__sign_in__date__gte=thirty_days_ago
    ).annotate(
        attendance_count=Count('attendance')
    ).order_by('-attendance_count')[:10]  # Show top 10 most active children
    
    # Prepare most active children data with attendance rate
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    most_active_children = []
    for child in active_children:
        total_days = (timezone.now().date() - thirty_days_ago).days
        attended_days = Attendance.objects.filter(
            child=child,
            sign_in__date__gte=thirty_days_ago
        ).count()
        attendance_rate = (attended_days / total_days * 100) if total_days > 0 else 0
        most_active_children.append({
            'child': child,
            'attendance_rate': f'{attendance_rate:.1f}'
        })

    # Get signed in children
    signed_in_children = Child.objects.filter(
        attendance__sign_in__date=selected_date,
        attendance__sign_out__isnull=True
    ).distinct()

    # Prepare data for template
    context = {
        'selected_date': selected_date,
        'center_name': center_name,
        'total_children': total_children,
        'currently_signed_in': total_attendance,
        'average_attendance_rate': f'{average_attendance_rate:.1f}',
        'avg_sign_in_time': avg_sign_in_time,
        'avg_sign_out_time': avg_sign_out_time,
        'peak_hour': peak_hour,
        'attendance_by_time': attendance_by_time,
        'attendances': display_attendances,
        'attendance_data': attendance_data,
        'current_time': current_time,
        'date_attendances': date_attendances,
        'rooms': rooms_with_data,
        'attendance_types': attendance_types,
        'attendance_counts': attendance_counts,
        'active_children': active_children,
        'signed_in_children': signed_in_children,
        'children_with_sign_in': {child.id: child for child in signed_in_children},
        'most_active_children': most_active_children
    }

    # Get attendance status counts
    attendance_types = ['Present', 'Absent']
    attendance_counts = [
        Attendance.objects.filter(
            child__center=center,
            sign_in__date=selected_date
        ).count(),
        Child.objects.filter(center=center).count() - total_attendance
    ]

    # Calculate date range for active children
    thirty_days_ago = selected_date - timedelta(days=30)

    # Handle PDF export
    if request.GET.get('export_pdf') == '1':
        return generate_pdf_report(attendances, 'daily', request)
    active_children = Child.objects.filter(
        center=center,
        attendance__sign_in__date__gte=thirty_days_ago
    ).annotate(
        attendance_count=Count('attendance')
    ).order_by('-attendance_count')[:10]  # Show top 10 most active children

    # Get currently signed in children
    currently_signed_in = children.filter(
        attendance__sign_in__date=today,
        attendance__sign_in__lte=current_time
    ).distinct().count()

    # Calculate present and absent children
    present_children = children.filter(
        attendance__sign_in__date=selected_date
    ).distinct().count()
    absent_children = total_children - present_children
    attendance_rate = (present_children / total_children * 100) if total_children > 0 else 0

    # Build final context
    context = {
        'attendances': attendances,
        'children': children,
        'center': center,
        'total_children': total_children,
        'present_children': present_children,
        'absent_children': absent_children,
        'attendance_rate': attendance_rate,
        'attendance_types': attendance_types,
        'attendance_counts': attendance_counts,
        'selected_date': selected_date,
        'attendance_by_time': attendance_by_time,
        'currently_signed_in': currently_signed_in,
        'average_attendance_rate': average_attendance_rate,
        'avg_sign_in_time': avg_sign_in_time,
        'avg_sign_out_time': avg_sign_out_time,
        'peak_hour': peak_hour,
        'active_children': active_children,
        'total_parents': Parent.objects.count()
    }

    # Handle PDF export
    if request.GET.get('export_pdf'):
        export_type = request.GET.get('export_type', 'daily')  # Default to daily
        return generate_pdf_report(attendances, export_type, request)

    return render(request, 'reports/admin_portal.html', context)
