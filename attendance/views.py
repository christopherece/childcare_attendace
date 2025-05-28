from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import Child, Parent, Attendance
from django.db.models import Q
import json
from django.utils import timezone

def dashboard(request):
    # Clear any existing messages before processing the request
    storage = messages.get_messages(request)
    storage.used = True
    
    if request.method == 'POST':
        child_id = request.POST.get('child_id')
        action = request.POST.get('action', 'sign_in')
        if child_id:
            child = get_object_or_404(Child, id=child_id)
            
            # Get all attendance records for today
            today_attendances = Attendance.objects.filter(
                child=child,
                created_at__date=timezone.now().date()
            ).order_by('timestamp')
            
            # Check the number of records for today
            if len(today_attendances) == 0:
                # No records - must be sign in
                if action == 'sign_out':
                    messages.error(request, f"{child.name} is not signed in. Please sign in first.")
                    return render(request, 'attendance/dashboard.html')
                # Create sign-in record
                Attendance.objects.create(
                    child=child,
                    parent=child.parent
                )
                messages.success(request, f"{child.name} has been signed in successfully!")
                return render(request, 'attendance/dashboard.html')
            
            elif len(today_attendances) == 1:
                # One record - can be either sign in or sign out
                if action == 'sign_in':
                    messages.error(request, f"{child.name} is already signed in. Please sign out first.")
                    return render(request, 'attendance/dashboard.html')
                # Create sign-out record
                Attendance.objects.create(
                    child=child,
                    parent=child.parent
                )
                messages.success(request, f"{child.name} has been signed out successfully!")
                return render(request, 'attendance/dashboard.html')
            
            elif len(today_attendances) == 2:
                # Two records - already signed out
                if action == 'sign_in':
                    messages.error(request, f"{child.name} is already signed out for today.")
                    return render(request, 'attendance/dashboard.html')
                # Already signed out - show error
                messages.error(request, f"{child.name} is already signed out for today.")
                return render(request, 'attendance/dashboard.html')
            
            # More than 2 records - should never happen
            messages.error(request, f"Error: Too many attendance records for {child.name} today. Please contact support.")
            return render(request, 'attendance/dashboard.html')
    
    return render(request, 'attendance/dashboard.html')

def search_children(request):
    query = request.GET.get('q', '')
    children = Child.objects.filter(
        Q(name__icontains=query) | Q(parent__name__icontains=query)
    ).values('id', 'name', 'parent__name', 'profile_picture')
    
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
        
        response_data.append({
            'id': child['id'],
            'name': child['name'],
            'parent__name': child['parent__name'],
            'profile_picture': profile_picture_url
        })
    
    return JsonResponse(response_data, safe=False)


def child_profile(request):
    child_id = request.GET.get('id')
    if not child_id:
        return JsonResponse({'error': 'Child ID is required'}, status=400)
    
    try:
        child = Child.objects.get(id=child_id)
        profile_picture_url = None
        if child.profile_picture:
            # Get the relative path from the profile_picture field
            # Extract the filename from the path
            filename = child.profile_picture.name.split('/')[-1]
            # Use the correct static URL
            profile_picture_url = f"/static/images/child_pix/{filename}"
        
        return JsonResponse({
            'profile_picture': profile_picture_url,
            'name': child.name,
            'parent_name': child.parent.name
        })
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found'}, status=404)

def attendance_records(request):
    # Group attendances by child and date
    attendance_data = []
    
    # Get all unique child IDs and dates
    unique_records = Attendance.objects.values('child_id', 'created_at__date').distinct()
    
    for record in unique_records:
        child_id = record['child_id']
        date = record['created_at__date']
        
        # Get the attendance records for this child and date
        attendances = Attendance.objects.filter(
            child_id=child_id,
            created_at__date=date
        ).order_by('timestamp')
        
        if attendances:
            child = attendances.first().child
            parent = attendances.first().parent
            
            # Get the first and last timestamps
            first_attendance = attendances.first()
            last_attendance = attendances.last()
            
            # Determine status based on number of records
            status = "Signed Out" if len(attendances) == 2 else "Signed In"
            
            attendance_data.append({
                'child': child,
                'parent': parent,
                'date': date,
                'status': status,
                'sign_in_time': first_attendance.timestamp,
                'sign_out_time': last_attendance.timestamp if len(attendances) == 2 else None,
                'created_at': first_attendance.created_at
            })
    
    return render(request, 'attendance/records.html', {
        'attendance_data': attendance_data
    })
