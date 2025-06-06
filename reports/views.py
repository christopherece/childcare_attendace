from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.functions import ExtractHour
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
<<<<<<< HEAD
import csv
import pytz
=======
>>>>>>> bf9ce64d4a125b805fe0271a7c445a408f80a7e9
from django.contrib import messages
from django.db import transaction
from attendance.models import Child, Parent, Attendance, Center, Teacher, Room
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.template.loader import render_to_string
from django.db.models import Prefetch

# Set default timezone to New Zealand
NZ_TIMEZONE = pytz.timezone('Pacific/Auckland')

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
        
        # Prepare data for template
        for attendance in attendances:
            attendance.status = 'Present' if attendance.sign_in else 'Absent'
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        filename = f"attendance_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create PDF using ReportLab
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=40,  # Increased top margin for header
            bottomMargin=30
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.fontSize = 12
        style.leading = 14
        
        # Create header with center name
        header = Paragraph("""
            <para alignment="center">
                <font size=20><b>{}</b></font>
                <br/>
                <font size=18><b>Attendance Report</b></font>
                <br/>
                <font size=12>Report Date: {}</font>
            </para>
        """.format(
            center.name if center else "Childcare Center",
            datetime.now().strftime('%B %d, %Y')
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
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9f9f9')),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 11),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,1), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6)
        ]))
        
        # Add footer
        footer = Paragraph("© 2025 ChildCare App | childcare.topitsolutions.co.nz", styles['Normal'])
        footer.style.fontSize = 10
        footer.style.alignment = 1  # Center align
        
        from reportlab.platypus import Spacer
        
        # Build document with spacing
        elements = [
            header,
            Spacer(1, 20),  # Add 20-point vertical space
            table,
            Spacer(1, 20),  # Add 20-point vertical space before footer
            footer
        ]
        doc.build(elements)
        
        return response
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('reports:admin_portal')


def admin_portal(request):
    """Admin portal view for managing attendance reports"""
    # Get today's date using timezone-aware datetime
    today = timezone.now().date()
    current_time = timezone.now()
    
    # Get the teacher's center information
    try:
        teacher = get_object_or_404(Teacher, user=request.user)
        center = teacher.center
        center_name = center.name if center else "All Centers"
    except Teacher.DoesNotExist:
        center_name = "All Centers"
        center = None
    
    # Get selected date from query parameters or use today
    selected_date_str = request.GET.get('date')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else today
    except (ValueError, TypeError):
        selected_date = today
    
    # Get teacher's rooms (if teacher exists)
    teacher_rooms = []
    if teacher:
        teacher_rooms = teacher.rooms.all()
    
    # Initialize empty attendances list if no center is found
    attendances = []
    
    # Get attendance records for the selected date if center exists
    if center:
        attendances = Attendance.objects.filter(
            child__center=center,
            sign_in__date=selected_date
        ).select_related('child', 'child__parent', 'child__room').order_by('child__name')

    # Handle PDF export if requested
    if request.GET.get('export_pdf') == '1':
        return generate_pdf_report(attendances, 'daily', request)

    # Get all children from this center with attendance records for the selected date
    children = Child.objects.filter(
        center=center,
        attendance__sign_in__date=selected_date
    ).distinct() if center else Child.objects.none()
    
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
<<<<<<< HEAD
    
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
        writer.writerow(['', '', '', ''])  # Empty row for spacing
        writer.writerow(['Childcare Attendance Report', '', '', ''])
        writer.writerow(['Center:', center_name, '', ''])
        writer.writerow(['Report Type:', {'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly'}[export_type], '', ''])
        writer.writerow(['Date Range:', f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}", '', ''])
        writer.writerow(['', '', '', ''])  # Empty row for spacing
        
        # Write column headers
        writer.writerow(['Child Name', 'Parent Name', 'Sign In Time', 'Sign Out Time', 'Status'])
        writer.writerow(['', '', '', '', ''])  # Empty row for spacing
        
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
            
            # Write attendance records
            if attendance_records.exists():
                for record in attendance_records:
                    writer.writerow([
                        child.name,
                        child.parent.name,
                        record.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p'),
                        record.sign_out.astimezone(NZ_TIMEZONE).strftime('%I:%M %p') if record.sign_out else 'Not signed out',
                        'Late' if record.late else ''
                    ])
            else:
                writer.writerow([
                    child.name,
                    child.parent.name,
                    'No attendance today',
                    '',
                    ''
                ])
            
            writer.writerow(['', '', '', '', ''])  # Empty row between children
        
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
=======
>>>>>>> bf9ce64d4a125b805fe0271a7c445a408f80a7e9

    # Calculate average attendance rate for the selected date
    all_children = Child.objects.filter(center=center)
    total_children = all_children.count()
    total_attendance = Attendance.objects.filter(
        child__in=all_children,
        sign_in__date=selected_date
    ).count()
    average_attendance_rate = (total_attendance / total_children * 100) if total_children > 0 else 0

    # Calculate time-based statistics (using ExtractHour for better handling of timestamp data)
    avg_sign_in_time = Attendance.objects.filter(
        child__center=center,
        sign_in__date=selected_date
    ).annotate(hour=ExtractHour('sign_in')).aggregate(avg_sign_in=Avg('hour'))['avg_sign_in']
    
    avg_sign_out_time = Attendance.objects.filter(
        child__center=center,
        sign_out__date=selected_date
    ).annotate(hour=ExtractHour('sign_out')).aggregate(avg_sign_out=Avg('hour'))['avg_sign_out']

    # Get peak attendance hour
    peak_hour = Attendance.objects.filter(
        child__center=center,
        sign_in__date=selected_date
    ).annotate(hour=ExtractHour('sign_in')).values('hour').annotate(count=Count('id')).order_by('-count').first()
    peak_hour = peak_hour.get('hour') if peak_hour else None

    # Get attendance by time
    attendance_by_time = Attendance.objects.filter(
        child__center=center,
        sign_in__date=selected_date
    ).annotate(hour=ExtractHour('sign_in')).values('hour').annotate(count=Count('id')).order_by('hour')

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
