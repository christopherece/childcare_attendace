from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('search/', views.search_children, name='search_children'),
    path('records/', views.attendance_records, name='attendance_records'),
    path('child-profile/', views.child_profile, name='child_profile'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('sign-out/', views.sign_out, name='sign_out'),
    path('admin_portal/', views.admin_portal, name='admin_portal'),
    path('profile/', views.profile, name='profile'),
    path('check-sign-in/', views.check_sign_in, name='check_sign_in'),
]
