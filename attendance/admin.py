from django.contrib import admin
from .models import Child, Parent, Attendance

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'parent__name')
    ordering = ('-created_at',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('child', 'parent', 'timestamp', 'created_at')
    list_filter = ('timestamp', 'child__parent')
    search_fields = ('child__name', 'parent__name')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('created_at',)
