from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('admin-portal/', views.admin_portal, name='admin_portal'),
]
