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
            timestamp__date=today,
            action_type='sign_in'
        ).first()
        
        if existing_sign_in:
            return JsonResponse({
                'already_signed_in': True,
                'sign_in_time': existing_sign_in.timestamp.strftime('%I:%M %p')
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
                        if Attendance.check_existing_record(child, 'sign_in'):
                            messages.error(request, f"{child.name} is already signed in today")
                            return redirect('attendance:dashboard')
                        
                        # Create new sign-in record
                        attendance = Attendance.objects.create(
                            child=child,
                            parent=child.parent,
                            center=child.center,
                            action_type='sign_in',
                            notes=notes
                        )
                        
                        # Check if this is the first sign-in of the day
                        if not Attendance.check_existing_record(child, 'sign_in'):
                            # Mark as late if after opening time
                            if attendance.timestamp.time() > child.center.opening_time:
                                attendance.late = True
                                attendance.save()
                                # Send late notification email
                                send_mail(
                                    subject='Late Sign-in Notification',
                                    message=f"Late sign-in for {child.name} at {attendance.timestamp.strftime('%I:%M %p')}",
                                    from_email=settings.EMAIL_HOST_USER,
                                    recipient_list=[child.parent.email, 'christopheranchetaece@gmail.com'],
                                    fail_silently=True
                                )
                        
                        messages.success(request, f"{child.name} has been signed in.")
                        return redirect('attendance:dashboard')
                        
                except IntegrityError:
                    messages.error(request, f"{child.name} is already signed in today.")
                    return redirect('attendance:dashboard')
                    
            elif action == 'sign_out':
                # Check if there's an existing sign-in today
                today = timezone.now().date()
                existing_sign_in = Attendance.objects.filter(
                    child=child,
                    timestamp__date=today,
                    action_type='sign_in'
                ).exists()
                
                if not existing_sign_in:
                    messages.error(request, f"{child.name} is not signed in today.")
                    return redirect('attendance:dashboard')
                    
                # Check if there's already a sign-out record today
                existing_sign_out = Attendance.objects.filter(
                    child=child,
                    timestamp__date=today,
                    action_type='sign_out'
                ).exists()
                
                if existing_sign_out:
                    messages.error(request, f"{child.name} is already signed out today.")
                    return redirect('attendance:dashboard')
                
                # Create sign-out record with current timestamp
                attendance = Attendance.objects.create(
                    child=child,
                    parent=child.parent,
                    center=child.center,
                    action_type='sign_out',
                    notes=notes,
                    prevent_sign_in_until_tomorrow=True
                )
                
                # The timestamp will be automatically set by the model's save method
                attendance.save()
                
                messages.success(request, f"{child.name} has been signed out.")
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
            latest_sign_in = records.filter(action_type='sign_in').last()
            if latest_sign_in:
                signed_in_children.append({
                    'child': child,
                    'sign_in_time': latest_sign_in.timestamp,
                    'late': latest_sign_in.late
                })
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).order_by('-timestamp')[:5]
    
    context = {
        'total_children': children.count(),
        'total_signed_in': len(signed_in_children),
        'total_signed_out': children.count() - len(signed_in_children),
        'recent_notifications': recent_notifications
    }
    
    return render(request, 'attendance/dashboard.html', context)

def search_children(request):
    query = request.GET.get('q', '')
    children = Child.objects.filter(
        Q(name__icontains=query) | Q(parent__name__icontains=query)
    ).values('id', 'name', 'parent__name', 'profile_picture')
    
    today = timezone.now().date()
    response_data = []
    
    for child in children:
        # Get today's attendance records
        records = Attendance.get_daily_attendance(child['id'], today)
        
        # Check attendance status
        attendance_status = None
        if records.exists():
            last_record = records.last()
            if last_record.action_type == 'sign_in':
                attendance_status = 'Signed In'
            else:
                attendance_status = 'Signed Out'
        else:
            attendance_status = 'Not Signed In'
        
        # Get profile picture URL
        profile_picture_url = child['profile_picture'] or '/static/images/child_pix/user-default.png'
        
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
        profile_picture_url = child.profile_picture.url if child.profile_picture else '/static/images/child_pix/user-default.png'
        
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
