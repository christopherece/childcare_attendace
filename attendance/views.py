from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from datetime import timedelta
from django.db import transaction, utils
from django.db.utils import IntegrityError
from datetime import datetime

from .models import Child, Attendance
from notifications.models import Notification
from django.db.models import Q
import json
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.template.loader import render_to_string

def check_sign_in(request):
    child_id = request.GET.get('child_id')
    if not child_id:
        return JsonResponse({'error': 'Child ID is required'}, status=400)
    
    try:
        child = Child.objects.get(id=child_id)
        today = timezone.now().date()
        existing_sign_in = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).first()
        
        if existing_sign_in:
            return JsonResponse({
                'already_signed_in': True,
                'sign_in_time': existing_sign_in.sign_in.strftime('%I:%M %p')
            })
        
        return JsonResponse({'already_signed_in': False})
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found'}, status=404)

def dashboard(request):
    # Handle form submission
    if request.method == 'POST':
        # Clear any existing messages before processing the request
        storage = messages.get_messages(request)
        storage.used = True
        
        # Process the form submission
        action = request.POST.get('action')
        child_id = request.POST.get('child_id')
        notes = request.POST.get('notes', '')
        
        try:
            child = Child.objects.get(id=child_id)
            
            if action == 'sign_in':
                try:
                    with transaction.atomic():
                        # Check if child is already signed in today
                        if Attendance.check_existing_record(child):
                            messages.error(request, f"{child.name} is already signed in today")
                            return redirect('attendance:dashboard')
                        
                        # Create sign-in record
                        attendance = Attendance.objects.create(
                            child=child,
                            parent=child.parent,
                            center=child.center,
                            sign_in=timezone.now(),
                            notes=notes
                        )
                        
                        # Send sign-in notification
                        # Prepare email context
                        context = {
                            'child_name': child.name,
                            'parent_name': child.parent.name,
                            'sign_in_time': attendance.sign_in.strftime('%I:%M %p'),
                            'center_name': child.center.name
                        }
                        
                        # Render the email template
                        html_message = render_to_string('emails/signin_notification.html', context)
                        
                        send_mail(
                            subject=f'Sign-in Notification - {child.name}',
                            message='Please view the attached email for details.',
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[child.parent.email, 'christopheranchetaece@gmail.com'],
                            html_message=html_message,
                            fail_silently=True
                        )
                        
                        messages.success(request, f"{child.name} has been signed in.")
                        return redirect('attendance:dashboard')
                        
                except IntegrityError:
                    messages.error(request, f"{child.name} is already signed in today.")
                    return redirect('attendance:dashboard')
                    
            elif action == 'sign_out':
                today = timezone.now().date()
                
                # Get the latest attendance record for today
                attendance = Attendance.objects.filter(
                    child=child,
                    sign_in__date=today
                ).latest('sign_in')
                
                # Get center name from the selected child
                center_name = child.center.name if child.center else 'Unknown Center'
                
                if not attendance:
                    messages.error(request, f"{child.name} is not signed in today.")
                    return redirect('attendance:dashboard')
                
                # Check if the child has already been signed out today
                if attendance.sign_out:
                    messages.error(request, f"{child.name} has already been signed out today at {attendance.sign_out.strftime('%I:%M %p')}")
                    return redirect('attendance:dashboard')
                
                try:
                    with transaction.atomic():
                        # Update sign-out time
                        attendance.sign_out = timezone.now()
                        attendance.notes = notes
                        attendance.save()
                        
                        # Send notification email
                        send_mail(
                            subject='Child Sign-out Notification',
                            message=f"{child.name} has been signed out at {attendance.sign_out.strftime('%I:%M %p')}",
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[child.parent.email, 'christopheranchetaece@gmail.com'],
                            fail_silently=True
                        )
                        
                        messages.success(request, f"{child.name} has been signed out.")
                        return redirect('attendance:dashboard')
                except Exception as e:
                    messages.error(request, f"Error signing out {child.name}: {str(e)}")
                    return redirect('attendance:dashboard')
                
        except Child.DoesNotExist:
            messages.error(request, "Child not found.")
            return redirect('attendance:dashboard')
    
    # For GET requests or after POST processing
    today = timezone.now().date()
    children = Child.objects.all()
    
    # Get signed in children with their attendance data
    signed_in_children = []
    for child in children:
        status = Attendance.get_today_status(child)
        if status == 'signed_in':
            # Get the latest sign-in record
            records = Attendance.get_daily_attendance(child, today)
            latest_sign_in = records.first()
            if latest_sign_in:
                signed_in_children.append({
                    'child': child,
                    'sign_in_time': latest_sign_in.sign_in,
                    'late': latest_sign_in.late
                })
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).order_by('-timestamp')[:5]
    
    # Get center name from the selected child
    center_name = ''
    if request.method == 'POST' and 'child_id' in request.POST:
        selected_child = get_object_or_404(Child, id=request.POST['child_id'])
        center_name = selected_child.center.name if selected_child.center else 'Unknown Center'
    
    context = {
        'total_children': children.count(),
        'total_signed_in': len(signed_in_children),
        'total_signed_out': children.count() - len(signed_in_children),
        'recent_notifications': recent_notifications,
        'center_name': center_name
    }
    
    return render(request, 'attendance/dashboard.html', context)

def search_children(request):
    query = request.GET.get('q', '')
    children = Child.objects.filter(
        Q(name__icontains=query) | Q(parent__name__icontains=query)
    ).prefetch_related('center')
    
    today = timezone.now().date()
    results = []
    
    for child in children:
        # Get today's attendance record
        record = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).first()
        
        # Check attendance status
        attendance_status = None
        if record:
            if record.sign_out:
                attendance_status = 'Signed Out'
            else:
                attendance_status = 'Signed In'
        else:
            attendance_status = 'Not Signed In'
        
        # Get profile picture URL
        profile_picture_url = child.profile_picture.url if child.profile_picture else '/static/images/child_pix/user-default.png'
        
        results.append({
            'id': child.id,
            'name': child.name,
            'parent__name': child.parent.name if child.parent else 'No parent assigned',
            'center_name': child.center.name if child.center else 'Unknown Center',
            'profile_picture': profile_picture_url,
            'attendance_status': attendance_status
        })
    
    return JsonResponse(results, safe=False)


def child_profile(request):
    child_id = request.GET.get('id')
    if not child_id:
        return JsonResponse({'error': 'Child ID is required'}, status=400)
    
    try:
        child = Child.objects.get(id=child_id)
        profile_picture_url = child.profile_picture.url if child.profile_picture else '/static/images/child_pix/user-default.png'
        
        # Get today's attendance record for this child
        today = timezone.now().date()
        record = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).first()
        
        # Check attendance status
        is_signed_in = bool(record)
        is_signed_out = bool(record and record.sign_out)
        
        # Determine attendance status
        attendance_status = 'Not Signed In'
        if record:
            if record.sign_out:
                attendance_status = 'Signed Out'
            else:
                attendance_status = 'Signed In'
        
        # Handle profile picture URL
        if child.profile_picture:
            profile_picture_url = child.profile_picture.url
        else:
            # Use absolute URL for static files
            profile_picture_url = request.build_absolute_uri('/static/images/child_pix/user-default.png')
        
        return JsonResponse({
            'profile_picture': profile_picture_url,
            'name': child.name,
            'parent_name': child.parent.name,
            'attendance_status': attendance_status,
            'is_signed_in': is_signed_in,
            'is_signed_out': is_signed_out
        })
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found'}, status=404)

def attendance_records(request):
    # Get all children
    children = Child.objects.all().order_by('name')
    
    # Get today's date
    today = timezone.now().date()
    
    # Get all attendance records for today
    todays_attendances = Attendance.objects.filter(sign_in__date=today).order_by('child_id', 'sign_in')
    
    # Create a dictionary to store attendance status for each child
    attendance_status = {}
    
    # Process attendance records
    for attendance in todays_attendances:
        if attendance.child_id not in attendance_status:
            attendance_status[attendance.child_id] = []
        # We no longer track action_type, so just store the attendance record
        if record:
            if record.sign_out:
                child_status['status'] = 'Signed Out'
            else:
                child_status['status'] = 'Signed In'
        else:
            child_status['status'] = 'Not Signed In'
        
        children_data.append(child_status)
    
    # Process records to group by child and date
    attendance_data = []
    current_child = None
    current_date = None
    current_records = []
    
    for attendance in todays_attendances:
        if (attendance.child_id != current_child) or (attendance.sign_in.date() != current_date):
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
                    'sign_in_time': first_attendance.sign_in,
                    'sign_out_time': last_attendance.sign_out if len(current_records) == 2 else None,
                })
                
            # Start new group
            current_child = attendance.child_id
            current_date = attendance.sign_in.date()
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
            'sign_in_time': first_attendance.sign_in,
            'sign_out_time': last_attendance.sign_out if len(current_records) == 2 else None,
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
