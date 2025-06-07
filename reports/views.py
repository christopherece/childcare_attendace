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


def generate_pdf_report(attendances, report_type, request):
    """Generate PDF report with professional layout"""
    try:
        # Get the center from the first attendance (assuming all attendances are from the same center)
        if attendances:
            center = attendances[0].child.center
        else:
            center = None
            
        # Get selected date from request
        selected_date = request.GET.get('date')
        if selected_date:
            try:
                selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                selected_date = None
        
        # Prepare data for template
        for attendance in attendances:
            attendance.status = 'Present' if attendance.sign_in else 'Absent'
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        filename = f"attendance_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create PDF using ReportLab with landscape orientation
        doc = SimpleDocTemplate(
            response,
            pagesize=landscape(A4),
            rightMargin=40,
            leftMargin=40,
            topMargin=50,
            bottomMargin=40
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.fontSize = 12
        style.leading = 14
        
        # Create header with center name and report date
        header = Paragraph("""
            <para alignment="center">
                <font size=24><b>{}</b></font>
                <br/>
                <font size=20><b>Attendance Report</b></font>
                <br/>
                <font size=14>Report Date: {}</font>
                <br/>
                <font size=14>Attendance Date: {}</font>
            </para>
        """.format(
            center.name if center else "Childcare Center",
            datetime.now().strftime('%B %d, %Y'),
            selected_date.strftime('%B %d, %Y') if selected_date else 'Today'
        ), styles['Normal'])
        
        # Create table data
        data = [['Child Name', 'Sign In Time', 'Sign Out Time', 'Status', 'Notes']]
        for attendance in attendances:
            data.append([
                attendance.child.name,
                attendance.sign_in.strftime('%I:%M %p') if attendance.sign_in else '-',
                attendance.sign_out.strftime('%I:%M %p') if attendance.sign_out else '-',
                attendance.status,
                attendance.notes or '-'
            ])
        
        # Create table
        table = Table(data)
        
        # Add table style
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 14),
            ('BOTTOMPADDING', (0,0), (-1,0), 15),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9f9f9')),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,1), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 15),
            ('RIGHTPADDING', (0,0), (-1,-1), 15),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8)
        ]))
        
        # Add footer with larger font and better spacing
        footer = Paragraph("""
            <para alignment="center">
                <font size=12>© 2025 ChildCare App | childcare.topitsolutions.co.nz</font>
                <br/>
                <font size=10>Page <pageNumber/></font>
            </para>
        """, styles['Normal'])
        
        from reportlab.platypus import Spacer
        
        # Build document with improved spacing
        elements = [
            header,
            Spacer(1, 30),  # Increased vertical space
            table,
            Spacer(1, 40),  # Increased vertical space before footer
            footer
        ]
        doc.build(elements)
        
        return response
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('reports:admin_portal')


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
    today = timezone.now().date()
    current_time = timezone.now()
    
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
    
    # Get selected date from query parameters or use today
    selected_date_str = request.GET.get('date')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else today
    except (ValueError, TypeError):
        selected_date = today
    
    # Get room data and attendance statistics
    rooms = Room.objects.filter(center=center).prefetch_related(
        'children',
        'children__attendance_set'
    )
    
    # Calculate attendance statistics for each room
    room_stats = []
    current_time = timezone.now()
    
    for room in rooms:
        # Get all children in this room
        children = room.children.all()
        total_children = children.count()
        
        # Count signed in children
        signed_in_children = 0
        for child in children:
            attendance = Attendance.get_daily_attendance(child, selected_date)
            if attendance:
                signed_in_children += 1
        
        # Calculate attendance percentage
        attendance_percentage = (signed_in_children / total_children * 100) if total_children > 0 else 0
        
        # Add room stats to list
        room_stats.append({
            'room': room,
            'total_children': total_children,
            'signed_in_children': signed_in_children,
            'attendance_percentage': attendance_percentage
        })
    
    # Get attendance records for statistics
    attendance_records = Attendance.objects.filter(
        child__center=center,
        sign_in__date=selected_date
    ).select_related('child')
    
    # Calculate overall statistics
    total_children = sum(stat['total_children'] for stat in room_stats)
    total_signed_in = sum(stat['signed_in_children'] for stat in room_stats)
    
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
    
    # Get all attendance records for the selected date (for display)
    display_attendances = Attendance.objects.filter(
        sign_in__date=selected_date
    ).select_related('child', 'child__parent', 'child__room').order_by('child__name')

    # Handle PDF export if requested
    if request.GET.get('export_pdf') == '1':
        return generate_pdf_report(display_attendances, 'daily', request)

    # Get all children in the system
    children = Child.objects.filter(center=center)
    
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

    # Calculate average attendance rate for the selected date
    total_children = children.count()
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
        if attendance.sign_in:
            total_sign_in_hours += attendance.sign_in.hour
            count_sign_in += 1
        if attendance.sign_out:
            total_sign_out_hours += attendance.sign_out.hour
            count_sign_out += 1
    
    if count_sign_in > 0:
        avg_sign_in_time = total_sign_in_hours / count_sign_in
    if count_sign_out > 0:
        avg_sign_out_time = total_sign_out_hours / count_sign_out

    # Get peak attendance hour
    peak_hour = None
    peak_count = 0
    hour_counts = {}
    
    for attendance in display_attendances:
        if attendance.sign_in:
            hour = attendance.sign_in.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
            if hour_counts[hour] > peak_count:
                peak_count = hour_counts[hour]
                peak_hour = hour

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
        'rooms': rooms,
        'room_stats': room_stats,
        'total_children': total_children,
        'currently_signed_in': currently_signed_in,
        'overall_attendance_percentage': overall_attendance_percentage,
        'attendances': display_attendances,
        'children': children,
        'date': selected_date,
        'center': center,
        'center_name': center_name,
        'avg_sign_in_time': avg_sign_in_time,
        'avg_sign_out_time': avg_sign_out_time,
        'peak_hour': peak_hour,
        'attendance_by_time': attendance_by_time,
        'status_filter': status_filter,
        'room_filter': room_filter,
        'average_attendance_rate': average_attendance_rate,
        'attendance_data': attendance_data,
        'rooms_with_data': rooms_with_data,
        'attendance_types': attendance_types,
        'attendance_counts': attendance_counts
    }
    
    return render(request, 'reports/admin_portal.html', context)

    # Calculate date range for active children
    thirty_days_ago = selected_date - timedelta(days=30)

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
