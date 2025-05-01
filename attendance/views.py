from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Child, Parent, Attendance
from django.db.models import Q
import json
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

def dashboard(request):
    # Clear any existing messages before processing the request
    storage = messages.get_messages(request)
    storage.used = True
    
    if request.method == 'POST':
        child_id = request.POST.get('child_id')
        action = request.POST.get('action', 'sign_in')
        if child_id:
            child = get_object_or_404(Child, id=child_id)
            
            if action == 'sign_in':
                # Always allow sign-in at the start of the day
                today = timezone.now().date()
                records = Attendance.get_daily_attendance(child, today)
                if len(records) > 0 and records.last().action_type == 'sign_in':
                    messages.error(request, f"{child.name} is already signed in today.")
                    return render(request, 'attendance/dashboard.html')
                
                # Create new sign-in record
                Attendance.objects.create(
                    child=child,
                    parent=child.parent,
                    action_type='sign_in'
                )
                messages.success(request, f"{child.name} has been signed in.")

                # Send Email
                try:
                    # Prepare email context
                    context = {
                        'child_name': child.name,
                        'action_type': 'Signed In',
                        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Render HTML template
                    html_message = render_to_string('emails/attendance_notification.html', context)
                    
                    send_mail(
                        'Childcare Attendance Notification',
                        'Please view this email in a HTML-compatible email client.',
                        settings.EMAIL_HOST_USER,
                        [child.parent.email, 'christopheranchetaece@gmail.com'],
                        fail_silently=True,
                        html_message=html_message
                    )
                    print(f"Email sent successfully to {child.parent.email}")
                except Exception as e:
                    print(f"Email sending failed: {str(e)}")
                    print(f"Failed to send email to: {child.parent.email}")
                    messages.error(request, "Failed to send notification email. Please check the email configuration.")

                return render(request, 'attendance/dashboard.html')
            
            if action == 'sign_out':
                if not Attendance.can_sign_out(child):
                    messages.error(request, f"{child.name} cannot be signed out today. ")
                    return render(request, 'attendance/dashboard.html')
                
                # Create new sign-out record
                Attendance.objects.create(
                    child=child,
                    parent=child.parent,
                    action_type='sign_out'
                )
                messages.success(request, f"{child.name} has been signed out.")

                # Send Email
                try:
                    # Prepare email context
                    context = {
                        'child_name': child.name,
                        'action_type': 'Signed Out',
                        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Render HTML template
                    html_message = render_to_string('emails/attendance_notification.html', context)
                    
                    send_mail(
                        'Childcare Attendance Notification',
                        'Please view this email in a HTML-compatible email client.',
                        settings.EMAIL_HOST_USER,
                        [child.parent.email, 'christopheranchetaece@gmail.com'],
                        fail_silently=False,
                        html_message=html_message
                    )
                    print(f"Email sent successfully to {child.parent.email}")
                except Exception as e:
                    # Log the error with more details
                    print(f"Email sending failed: {str(e)}")
                    print(f"Failed to send email to: {child.parent.email}")
                    print(f"Email configuration: {EMAIL_HOST_USER}")
                    messages.error(request, f"Failed to send notification email: {str(e)}")

                return render(request, 'attendance/dashboard.html')
    
    return render(request, 'attendance/dashboard.html')

def search_children(request):
    query = request.GET.get('q', '')
    children = Child.objects.filter(
        Q(name__icontains=query) | Q(parent__name__icontains=query)
    ).values('id', 'name', 'parent__name', 'profile_picture')
    
    # Get today's attendance records
    today = timezone.now().date()
    today_attendances = Attendance.objects.filter(
        timestamp__date=today
    ).values('child_id', 'timestamp')
    
    # Convert the QuerySet to a list and format the response
    response_data = []
    for child in children:
        # Get the relative path from the profile_picture field
        profile_picture_url = None
        if child['profile_picture']:
            try:
                # Extract just the filename from the path
                filename = child['profile_picture'].split('/')[-1]
                # Use the correct static URL
                profile_picture_url = f"/static/images/child_pix/{filename}"
            except Exception as e:
                print(f"Error building URL for profile picture: {e}")
                profile_picture_url = '/static/images/child_pix/user-default.png'
        else:
            profile_picture_url = '/static/images/child_pix/user-default.png'
        
        # Check attendance status
        attendance_status = None
        if child['id'] in [a['child_id'] for a in today_attendances]:
            # Get the latest attendance record for this child
            latest_attendance = next((a for a in today_attendances if a['child_id'] == child['id']), None)
            if latest_attendance:
                # If there's an even number of records, they're signed out
                child_records = [a for a in today_attendances if a['child_id'] == child['id']]
                if len(child_records) % 2 == 0:
                    attendance_status = 'Signed Out'
                else:
                    attendance_status = 'Signed In'

        response_data.append({
            'id': child['id'],
            'name': child['name'],
            'parent__name': child['parent__name'],
            'profile_picture': profile_picture_url,
            'attendance_status': attendance_status
        })
    
    return JsonResponse(response_data, safe=False)


def child_profile(request):
    child_id = request.GET.get('id')
    if not child_id:
        return JsonResponse({'error': 'Child ID is required'}, status=400)
    
    try:
        child = Child.objects.get(id=child_id)
        profile_picture_url = f"/static/images/child_pix/{child.profile_picture.name.split('/')[-1]}" if child.profile_picture else '/static/images/child_pix/user-default.png'
        
        # Get today's attendance records for this child
        today = timezone.now().date()
        child_records = Attendance.objects.filter(
            child=child,
            created_at__date=today
        ).order_by('created_at')
        
        # Determine attendance status
        attendance_status = None
        if child_records.exists():
            if len(child_records) % 2 == 0:
                attendance_status = 'Signed Out'
            else:
                attendance_status = 'Signed In'
        
        return JsonResponse({
            'profile_picture': profile_picture_url,
            'name': child.name,
            'parent_name': child.parent.name,
            'attendance_status': attendance_status
        })
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found'}, status=404)

def attendance_records(request):
    # Get all children
    children = Child.objects.all().order_by('name')
    
    # Get today's date
    today = timezone.now().date()
    
    # Get all attendance records for today
    todays_attendances = Attendance.objects.filter(timestamp__date=today).order_by('child_id', 'timestamp')
    
    # Create a dictionary to store attendance status for each child
    attendance_status = {}
    
    # Process attendance records
    for attendance in todays_attendances:
        if attendance.child_id not in attendance_status:
            attendance_status[attendance.child_id] = []
        attendance_status[attendance.child_id].append(attendance.action_type)
    
    # Prepare data for template
    children_data = []
    for child in children:
        child_status = {
            'id': child.id,
            'name': child.name,
            'parent': child.parent.name if child.parent else 'No parent assigned',
            'last_action': None,
            'status': None,
            'center': child.center.name if child.center else 'No center assigned'
        }
        
        # Get today's attendance records for this child
        if child.id in attendance_status:
            records = attendance_status[child.id]
            child_status['last_action'] = records[-1]
            child_status['status'] = 'Signed Out' if len(records) % 2 == 0 else 'Signed In'
        else:
            child_status['status'] = 'Not Signed In'
        
        children_data.append(child_status)
    
    # Process records to group by child and date
    attendance_data = []
    current_child = None
    current_date = None
    current_records = []
    
    for attendance in todays_attendances:
        if (attendance.child_id != current_child) or (attendance.timestamp.date() != current_date):
            # Process previous group if we have one
            if current_records:
                first_attendance = current_records[0]
                last_attendance = current_records[-1]
                status = "Signed Out" if len(current_records) == 2 else "Signed In"
                
                attendance_data.append({
                    'child': first_attendance.child,
                    'parent': first_attendance.parent,
                    'date': current_date,
                    'status': status,
                    'sign_in_time': first_attendance.timestamp,
                    'sign_out_time': last_attendance.timestamp if len(current_records) == 2 else None,
                })
                
            # Start new group
            current_child = attendance.child_id
            current_date = attendance.timestamp.date()
            current_records = []
            
        current_records.append(attendance)
    
    # Process last group if any
    if current_records:
        first_attendance = current_records[0]
        last_attendance = current_records[-1]
        status = "Signed Out" if len(current_records) == 2 else "Signed In"
        
        attendance_data.append({
            'child': first_attendance.child,
            'parent': first_attendance.parent,
            'date': current_date,
            'status': status,
            'sign_in_time': first_attendance.timestamp,
            'sign_out_time': last_attendance.timestamp if len(current_records) == 2 else None,
        })
    
    return render(request, 'attendance/records.html', {
        'children_data': children_data
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_portal(request):
    return redirect('reports:admin_portal')

def sign_in(request):
    return redirect('login')

def sign_out(request):
    logout(request)
    return redirect('attendance:sign_in')
