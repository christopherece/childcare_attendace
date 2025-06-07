from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
import pytz
from .models import Child, Attendance

# Set default timezone to New Zealand
NZ_TIMEZONE = pytz.timezone('Pacific/Auckland')

from .models import Teacher, Center, Child, Attendance
from .forms import TeacherProfileForm
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

@login_required
def logout_view(request):
    """Handle user logout"""
    if request.method in ['GET', 'POST']:
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('attendance:login')
    return redirect('attendance:login')

# Original imports continue below...
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.template.loader import render_to_string

def child_detail(request, child_id):
    """View to display child details and their attendance records"""
    child = get_object_or_404(Child, id=child_id)
    
    # Get today's date
    today = timezone.now().date()
    
    # Get attendance records for this child
    attendance_records = Attendance.objects.filter(
        child=child,
        sign_in__date__gte=today - timedelta(days=7)  # Show last 7 days
    ).order_by('-sign_in')
    
    context = {
        'child': child,
        'attendance_records': attendance_records,
        'today': today
    }
    return render(request, 'attendance/child_detail.html', context)

def login_view(request):
    # If GET request, just show the login form
    if request.method == 'GET':
        return render(request, 'registration/login.html')
    
    # Handle POST request
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if not username or not password:
        messages.error(request, 'Please enter both username and password.')
        return render(request, 'registration/login.html', {
            'username': username,
            'password': ''  # Clear password field for security
        })
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('dashboard')
    else:
        messages.error(request, 'Invalid username or password.')
        return render(request, 'registration/login.html', {
            'username': username,
            'password': ''  # Clear password field for security
        })

@login_required
def check_sign_in(request):
    """Check if a child is already signed in for today"""
    child_id = request.GET.get('child_id')
    if not child_id:
        return JsonResponse({'error': 'Child ID is required'}, status=400)
    
    try:
        child = Child.objects.get(id=child_id)
        today = timezone.now().astimezone(NZ_TIMEZONE).date()
        
        # Check for existing sign-in today
        attendance = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).first()
        
        if attendance:
            if attendance.sign_out:
                # Child has already signed in and out today
                return JsonResponse({
                    'already_signed_in': False,
                    'error': 'Child has already signed in and out today'
                })
            else:
                # Child is currently signed in
                return JsonResponse({
                    'already_signed_in': True,
                    'sign_in_time': attendance.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p')
                })
        
        # No sign-in exists for today
        return JsonResponse({
            'already_signed_in': False
        })
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard(request):
    try:
        teacher = get_object_or_404(Teacher, user=request.user)
        today = timezone.now().astimezone(NZ_TIMEZONE).date()
        center = teacher.center
        children = Child.objects.filter(center=center)
        children_data = []
        signed_in_children = []

        if request.method == 'POST':
            action = request.POST.get('action')
            child_id = request.POST.get('child_id')
            notes = request.POST.get('notes', '')

            try:
                child = Child.objects.get(id=child_id)

                if action == 'sign_in':
                    try:
                        with transaction.atomic():
                            # Get today's date
                            today = timezone.now().astimezone(NZ_TIMEZONE).date()
                            
                            # Check for existing sign-in today
                            existing = Attendance.objects.filter(
                                child=child,
                                sign_in__date=today,
                                sign_out__isnull=True
                            ).first()
                            # Create new attendance record
                            attendance = Attendance.objects.create(
                                child=child,
                                parent=child.parent,
                                center=child.center,
                                sign_in=timezone.now().astimezone(NZ_TIMEZONE),
                                late=False,
                                notes=notes
                            )
                            
                            # Check if the child is late based on center's opening time
                            center_opening_time = child.center.opening_time
                            current_time = timezone.now().astimezone(NZ_TIMEZONE).time()
                            
                            if current_time > center_opening_time:
                                attendance.late = True
                                attendance.late_reason = 'Arrived after center opening time'
                                attendance.save()

                            # Prepare context for sign-in email
                            context = {
                                'child_name': child.name,
                                'parent_name': child.parent.name,
                                'sign_in_time': attendance.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p'),
                                'center_name': child.center.name,
                                'current_time': timezone.now().astimezone(NZ_TIMEZONE).strftime('%I:%M %p, %B %d, %Y')
                            }

                            html_message = render_to_string('emails/signin_notification.html', context)

                            send_mail(
                                subject=f'Sign-in Notification - {child.name}',
                                message='Please view the attached email for details.',
                                from_email=settings.EMAIL_HOST_USER,
                                recipient_list=[child.parent.email, 'christopheranchetaece@gmail.com'],
                                html_message=html_message,
                                fail_silently=True
                            )

                            messages.success(request, f"{child.name} signed in successfully!")
                            return redirect('attendance:dashboard')
                    except Exception as e:
                        messages.error(request, f"Error signing in {child.name}: {str(e)}")
                        return redirect('attendance:dashboard')

                elif action == 'sign_out':
                    records = Attendance.get_daily_attendance(child, today)
                    latest_record = records.first()

                    if not latest_record:
                        messages.error(request, f"{child.name} is not signed in today.")
                        return redirect('attendance:dashboard')

                    if latest_record.sign_out:
                        messages.error(request, f"{child.name} has already been signed out today.")
                        return redirect('attendance:dashboard')

                    try:
                        with transaction.atomic():
                            latest_record.sign_out = timezone.now().astimezone(NZ_TIMEZONE)
                            latest_record.notes = notes
                            latest_record.save()

                            # Prepare context for sign-out email
                            context = {
                                'child_name': child.name,
                                'parent_name': child.parent.name,
                                'sign_out_time': latest_record.sign_out.astimezone(NZ_TIMEZONE).strftime('%I:%M %p'),
                                'center_name': child.center.name,
                                'current_time': timezone.now().astimezone(NZ_TIMEZONE).strftime('%I:%M %p, %B %d, %Y')
                            }

                            html_message = render_to_string('emails/signout_notification.html', context)

                            send_mail(
                                subject=f'Sign-out Notification - {child.name}',
                                message='Please view the attached email for details.',
                                from_email=settings.EMAIL_HOST_USER,
                                recipient_list=[child.parent.email, 'christopheranchetaece@gmail.com'],
                                html_message=html_message,
                                fail_silently=True
                            )

                            messages.success(request, f"{child.name} signed out successfully!")
                            return redirect('attendance:dashboard')
                    except Exception as e:
                        messages.error(request, f"Error signing out {child.name}: {str(e)}")
                        return redirect('reports:admin_portal')

            except Child.DoesNotExist:
                messages.error(request, "Child not found.")
                return redirect('reports:admin_portal')
            except Exception as e:
                messages.error(request, f"Error processing request: {str(e)}")
                return redirect('reports:admin_portal')

        # For GET requests, show dashboard
        for child in children:
            todays_attendance = Attendance.objects.filter(
                child=child,
                sign_in__date=today
            ).order_by('-sign_in')
            
            latest_attendance = todays_attendance.first()
            is_signed_in = False
            if latest_attendance:
                is_signed_in = latest_attendance.sign_out is None
                if is_signed_in:
                    signed_in_children.append(child)
            
            children_data.append({
                'child': child,
                'is_signed_in': is_signed_in,
                'latest_attendance': latest_attendance
            })
        
        # Get recent notifications for this center
        recent_notifications = Notification.objects.filter(
            child__center=center
        ).order_by('-timestamp')[:5]
        
        context = {
            'total_children': len(children),
            'total_signed_in': len(signed_in_children),
            'total_signed_out': len(children) - len(signed_in_children),
            'recent_notifications': recent_notifications,
            'center_name': center.name if center else 'Unknown Center',
            'children_data': children_data
        }
        
        return render(request, 'attendance/dashboard.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('attendance:profile')
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('attendance:profile')

@login_required
def search_children(request):
    """Search for children in teacher's center based on name or parent name"""
    try:
        query = request.GET.get('q', '')
        room_id = request.GET.get('room', '')
        teacher = get_object_or_404(Teacher, user=request.user)
        center = teacher.center
        
        # Normalize query to lowercase and split into words
        query_words = query.lower().split()
        
        # Create Q objects for each word in both child name and parent name
        name_q = Q()
        for word in query_words:
            name_q |= Q(name__icontains=word) | Q(parent__name__icontains=word)
        
        # Search in both child name and parent name fields
        children = Child.objects.filter(
            name_q
        ).distinct()
        
        # Apply room filter if specified
        if room_id:
            children = children.filter(room_id=room_id)
        
        today = timezone.now().astimezone(NZ_TIMEZONE).date()
        
        data = []
        for child in children:
            # Get the latest attendance record for today
            latest_attendance = Attendance.objects.filter(
                child=child,
                sign_in__date=today
            ).order_by('-sign_in').first()
            
            status = 'Not Signed In'
            last_action = None
            
            if latest_attendance:
                if latest_attendance.sign_out:
                    status = 'Signed Out'
                    last_action = latest_attendance.sign_out.astimezone(NZ_TIMEZONE).strftime('%I:%M %p')
                else:
                    status = 'Signed In'
                    last_action = latest_attendance.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p')
            
            data.append({
                'id': child.id,
                'name': child.name,
                'parent': child.parent.name if child.parent else 'No Parent',
                'center': child.center.name if child.center else 'Unknown Center',
                'status': status,
                'last_action': last_action,
                'profile_picture': child.profile_picture.url if child.profile_picture else '/static/images/child_pix/user-default.png'
            })
        
        return JsonResponse(data, safe=False)
    
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Teacher not found'}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in search_children: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def rooms(request):
    """Get all rooms for the teacher's center"""
    try:
        teacher = get_object_or_404(Teacher, user=request.user)
        center = teacher.center
        rooms = Room.objects.filter(center=center).values('id', 'name')
        return JsonResponse(list(rooms), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def child_profile(request):
    child_id = request.GET.get('id')
    if not child_id:
        return JsonResponse({'error': 'Child ID is required'}, status=400)
    
    try:
        child = Child.objects.get(id=child_id)
        profile_picture_url = child.profile_picture.url if child.profile_picture else request.build_absolute_uri('/static/images/child_pix/user-default.png')
        
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
            profile_picture_url = request.build_absolute_uri('/media/child_pix/user-default.png')
        
        # Get the latest attendance record for today
        today = timezone.now().astimezone(NZ_TIMEZONE).date()
        latest_attendance = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).order_by('-sign_in').first()
        
        status = 'Not Signed In'
        last_action = None
        
        if latest_attendance:
            if latest_attendance.sign_out:
                status = 'Signed Out'
                last_action = latest_attendance.sign_out.astimezone(NZ_TIMEZONE).strftime('%I:%M %p')
            else:
                status = 'Signed In'
                last_action = latest_attendance.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p')
        
        return JsonResponse({
            'profile_picture': profile_picture_url,
            'name': child.name,
            'parent': child.parent.name if child.parent else 'No Parent',
            'center': child.center.name if child.center else 'Unknown Center',
            'status': status,
            'last_action': last_action
        })
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found'}, status=404)

def attendance_records(request):
    # Get today's date in NZ timezone
    today = timezone.now().astimezone(NZ_TIMEZONE).date()
    
    # Get children from the current teacher's center and rooms
    try:
        teacher = get_object_or_404(Teacher, user=request.user)
        center = teacher.center
        
        # If no rooms are assigned, get all rooms from the teacher's center
        if not teacher.rooms.exists():
            teacher_rooms = Room.objects.filter(center=center)
        else:
            teacher_rooms = teacher.rooms.all()
        
        # Debug logging
        print(f"Teacher found: {teacher.user.username}")
        print(f"Center: {center.name if center else 'None'}")
        print(f"Rooms assigned: {', '.join(room.name for room in teacher_rooms)}")
        
        # Get all children from the center
        children = Child.objects.filter(center=center).order_by('name')
        print(f"Children found: {children.count()}")
        for child in children:
            print(f"Child: {child.name}, Room: {child.room.name if child.room else 'None'}")
        
        # Get attendance records for today for all children in the center
        todays_attendances = Attendance.objects.filter(
            child__center=center,
            sign_in__date=today
        ).order_by('child_id', 'sign_in')
        print(f"Attendance records found: {todays_attendances.count()}")
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found')
        return redirect('attendance:profile')
    
    # Get attendance records for today for children in teacher's rooms
    todays_attendances = Attendance.objects.filter(
        child__center=center,
        child__room__in=teacher_rooms,
        sign_in__date=today
    ).order_by('child_id', 'sign_in')
    
    # Group attendances by child
    attendance_data = []
    current_child = None
    current_records = []
    
    for attendance in todays_attendances:
        if attendance.child_id != current_child:
            if current_child is not None:
                # Process previous child's records
                attendance_data.append({
                    'child': current_child,
                    'records': current_records
                })
            current_child = attendance.child
            current_records = []
        
        # Get attendance status
        status = 'Signed In'
        if attendance.sign_out:
            status = 'Signed Out'
        
        current_records.append({
            'sign_in': attendance.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p'),
            'sign_out': attendance.sign_out.astimezone(NZ_TIMEZONE).strftime('%I:%M %p') if attendance.sign_out else None,
            'status': status,
            'notes': attendance.notes
        })
    
    # Add the last child's records
    if current_child is not None:
        attendance_data.append({
            'child': current_child,
            'records': current_records
        })
    
    # Get children without attendance records today
    for child in children:
        if child.id not in [d['child'].id for d in attendance_data]:
            attendance_data.append({
                'child': child,
                'records': []
            })
    
    context = {
        'attendance_data': attendance_data,
        'today': today.strftime('%B %d, %Y')
    }
    return render(request, 'attendance/attendance_records.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_portal(request):
    return redirect('reports:admin_portal')

@login_required
def sign_in(request):
    """Handle child sign-in"""
    try:
        if request.method == 'POST':
            child_id = request.POST.get('child_id')
            if not child_id:
                return JsonResponse({'error': 'Child ID is required'}, status=400)

            child = get_object_or_404(Child, id=child_id)
            
            # Check if child is already signed in today
            if Attendance.check_existing_record(child):
                existing_record = Attendance.get_today_record(child)
                return JsonResponse({
                    'error': 'Child has already signed in today at ' + existing_record.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p'),
                    'status': 'Already Signed In',
                    'existing_sign_in': existing_record.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p')
                }, status=400)

            # Create new attendance record
            attendance = Attendance.objects.create(
                child=child,
                parent=child.parent,
                center=child.center,
                sign_in=timezone.now().astimezone(NZ_TIMEZONE)
            )

            # Create notification
            Notification.objects.create(
                child=child,
                parent=child.parent,
                teacher=request.user.teacher,
                center=child.center,
                title=f"Sign In: {child.name}",
                message=f"{child.name} has been signed in to {child.center.name} at {attendance.sign_in.strftime('%I:%M %p')}"
            )

            return JsonResponse({
                'success': True,
                'sign_in_time': attendance.sign_in.strftime('%I:%M %p'),
                'status': 'Signed In'
            })
        
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    except Exception as e:
        import traceback
        print(f"Error in sign_in: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def sign_out(request):
    """Handle child sign-out"""
    try:
        if request.method == 'POST':
            child_id = request.POST.get('child_id')
            if not child_id:
                return JsonResponse({'error': 'Child ID is required'}, status=400)

            child = get_object_or_404(Child, id=child_id)
            today = timezone.now().astimezone(NZ_TIMEZONE).date()

            # Get today's attendance record for this child
            attendance = Attendance.objects.filter(
                child=child,
                sign_in__date=today,
                sign_out__isnull=True
            ).order_by('-sign_in').first()

            if not attendance:
                return JsonResponse({'error': 'No active sign-in for this child today'}, status=400)

            # Update the attendance record with sign-out time
            attendance.sign_out = timezone.now().astimezone(NZ_TIMEZONE)
            attendance.save()

            # Create notification
            Notification.objects.create(
                child=child,
                parent=child.parent,
                teacher=request.user.teacher,
                center=child.center,
                title=f"Sign Out: {child.name}",
                message=f"{child.name} has been signed out from {child.center.name} at {attendance.sign_out.strftime('%I:%M %p')}"
            )

            # Redirect to dashboard after successful sign-out
            return redirect('attendance:dashboard')
        
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    except Exception as e:
        import traceback
        print(f"Error in sign_out: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def profile(request):
    """Display teacher's profile and center information"""
    try:
        teacher = get_object_or_404(Teacher, user=request.user)
        center = teacher.center
        
        # Get teacher's assigned rooms first
        teacher_rooms = teacher.rooms.all()
        
        if request.method == 'POST':
            form = TeacherProfileForm(request.POST, request.FILES, instance=teacher)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('attendance:profile')
        else:
            form = TeacherProfileForm(instance=teacher)
        
        # Get attendance stats
        today = timezone.now().date()
        children = Child.objects.filter(center=center)
        total_children = children.count()
        signed_in_children = children.filter(
            attendance__sign_in__date=today
        ).distinct().count()
        
        # Calculate average attendance rate for last 30 days
        thirty_days_ago = today - timedelta(days=30)
        total_attendance_records = Attendance.objects.filter(
            child__center=center,
            sign_in__date__gte=thirty_days_ago
        ).count()
        total_possible_attendances = children.count() * 30
        average_attendance_rate = (total_attendance_records / total_possible_attendances) * 100 if total_possible_attendances > 0 else 0
        
        # Get children in each room
        room_children = {}
        for room in teacher_rooms:
            children = Child.objects.filter(center=center, room=room)
            room_children[room] = children
        
        return render(request, 'attendance/profile.html', {
            'teacher': teacher,
            'center': center,
            'total_children': total_children,
            'signed_in_children': signed_in_children,
            'average_attendance_rate': round(average_attendance_rate, 1),
            'teacher_rooms': teacher_rooms,
            'room_children': room_children,
            'form': form
        })
    except Teacher.DoesNotExist:
        messages.error(request, 'You are not a teacher')
        return redirect('attendance:dashboard')
