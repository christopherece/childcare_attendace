from django.contrib import admin
from .models import Child, Parent, Attendance, Center

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'capacity', 'created_at')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('capacity',)
    ordering = ('name',)

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')
    ordering = ('-created_at',)

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'center', 'created_at')
    list_filter = ('parent', 'center')
    search_fields = ('name', 'parent__name', 'center__name')
    ordering = ('-created_at',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('child', 'parent', 'center', 'timestamp', 'created_at')
    list_filter = ('timestamp', 'child__parent', 'center')
    search_fields = ('child__name', 'parent__name', 'center__name')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('created_at',)
