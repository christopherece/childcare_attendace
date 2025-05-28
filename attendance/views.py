from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Child, Parent, Attendance
from django.db.models import Q
import json
from django.utils import timezone

def dashboard(request):
    if request.method == 'POST':
        child_id = request.POST.get('child_id')
        action = request.POST.get('action', 'sign_in')
        if child_id:
            child = get_object_or_404(Child, id=child_id)
            
            # Check if the child already has an attendance record for today
            existing_attendance = Attendance.objects.filter(
                child=child,
                created_at__date=timezone.now().date()
            ).first()
            
            if existing_attendance:
                if action == 'sign_in':
                    return render(request, 'attendance/dashboard.html', {
                        'error_message': f"{child.name} already has an attendance record for today."
                    })
                # For sign out, create a new record instead of updating
                Attendance.objects.create(
                    child=child,
                    parent=child.parent
                )
                return redirect('attendance:attendance_records')
            
            # Create new attendance record for sign-in
            Attendance.objects.create(
                child=child,
                parent=child.parent
            )
            return redirect('attendance:attendance_records')
    return render(request, 'attendance/dashboard.html')

def search_children(request):
    query = request.GET.get('q', '')
    children = Child.objects.filter(
        Q(name__icontains=query) | Q(parent__name__icontains=query)
    ).values('id', 'name', 'parent__name')
    return JsonResponse(list(children), safe=False)

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
