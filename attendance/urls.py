from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('search/', views.search_children, name='search_children'),
    path('records/', views.attendance_records, name='attendance_records'),
    path('child-profile/', views.child_profile, name='child_profile'),
]
