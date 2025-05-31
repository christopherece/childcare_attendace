from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
import pytz
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Teacher, Center, Child, Attendance
from .forms import TeacherProfileForm

# Set default timezone to New Zealand
NZ_TIMEZONE = pytz.timezone('Pacific/Auckland')
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

@login_required
@user_passes_test(lambda u: u.is_staff)
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
                            if Attendance.check_existing_record(child):
                                messages.error(request, f"{child.name} is already signed in today")
                                return redirect('attendance:dashboard')

                            attendance = Attendance.objects.create(
                                child=child,
                                parent=child.parent,
                                center=child.center,
                                sign_in=timezone.now().astimezone(NZ_TIMEZONE),
                                late=False,  # We'll set this based on the center's opening time
                                notes=notes
                            )
                            
                            # Check if the child is late based on center's opening time
                            center_opening_time = child.center.opening_time
                            current_time = timezone.now().astimezone(NZ_TIMEZONE).time()
                            
                            if current_time > center_opening_time:
                                attendance.late = True
                                attendance.late_reason = 'Arrived after center opening time'
                                attendance.save()

                            context = {
                                'child_name': child.name,
                                'parent_name': child.parent.name,
                                'sign_in_time': attendance.sign_in.astimezone(NZ_TIMEZONE).strftime('%I:%M %p'),
                                'center_name': child.center.name
                            }

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
                    except IntegrityError:
                        messages.error(request, f"{child.name} is already signed in today")
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
                        return redirect('attendance:dashboard')

            except Child.DoesNotExist:
                messages.error(request, "Child not found.")
                return redirect('attendance:dashboard')
            except Exception as e:
                messages.error(request, f"Error processing request: {str(e)}")
                return redirect('attendance:dashboard')

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
@user_passes_test(lambda u: u.is_staff)
def search_children(request):
    """Search for children in teacher's center based on name or parent name"""
    query = request.GET.get('q', '')
    teacher = get_object_or_404(Teacher, user=request.user)
    center = teacher.center
    
    # Get children from this center that match the search query
    children = Child.objects.filter(
        Q(center=center) & (Q(name__icontains=query) | Q(parent__name__icontains=query))
    ).select_related('parent', 'center')
    
    # Format the results
    results = []
    today = timezone.now().date()
    for child in children:
        # Get today's attendance record
        record = Attendance.objects.filter(
            child=child,
            sign_in__date=today
        ).first()
        
        # Check attendance status
        attendance_status = 'Not Signed In'
        if record:
            if record.sign_out:
                attendance_status = 'Signed Out'
            else:
                attendance_status = 'Signed In'
        
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
            'sign_in_time': attendance.sign_in.astimezone(NZ_TIMEZONE),
            'sign_out_time': last_attendance.sign_out.astimezone(NZ_TIMEZONE) if len(current_records) == 2 else None,
        })
    
    return render(request, 'attendance/records.html', {
        'children_data': attendance_data
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

@login_required
@user_passes_test(lambda u: u.is_staff)
def profile(request):
    """Display teacher's profile and center information"""
    teacher = get_object_or_404(Teacher, user=request.user)
    
    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('attendance:profile')
    else:
        form = TeacherProfileForm(instance=teacher)
    
    # Get today's date
    today = timezone.now().date()
    
    # Get attendance statistics for the teacher's center
    center = teacher.center
    if center:
        # Get total children in the center
        total_children = Child.objects.filter(center=center).count()
        
        # Get children signed in today
        signed_in_children = Child.objects.filter(
            center=center,
            attendance__sign_in__date=today
        ).distinct().count()
        
        # Get average attendance rate for the last 30 days
        thirty_days_ago = today - timedelta(days=30)
        attendance_records = Attendance.objects.filter(
            child__center=center,
            sign_in__date__gte=thirty_days_ago
        ).count()
        total_possible_signins = Child.objects.filter(center=center).count() * 30
        average_attendance_rate = (attendance_records / total_possible_signins * 100) if total_possible_signins > 0 else 0
    else:
        total_children = 0
        signed_in_children = 0
        average_attendance_rate = 0
    
    context = {
        'teacher': teacher,
        'center': center,
        'total_children': total_children,
        'signed_in_children': signed_in_children,
        'average_attendance_rate': f'{average_attendance_rate:.1f}',
        'form': form
    }
    
    return render(request, 'attendance/profile.html', context)
