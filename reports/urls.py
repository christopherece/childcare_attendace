from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('admin-portal/', views.admin_portal, name='admin_portal'),
    path('child/<int:child_id>/', views.child_details, name='child_details'),
    path('child/<int:child_id>/attendance/', views.child_attendance_report, name='child_attendance_report'),
]
