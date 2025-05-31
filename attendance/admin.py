from django.contrib import admin
from django.db import models
from .models import Child, Parent, Attendance, Center, Teacher

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
    list_display = ('child', 'parent', 'center', 'sign_in', 'sign_out', 'notes')
    list_filter = (
        'sign_in', 
        'child__parent', 
        'center'
    )
    search_fields = ('child__name', 'parent__name', 'center__name', 'notes')
    ordering = ('-sign_in',)
    actions = ['export_as_csv']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Add annotations for better filtering
        return queryset.annotate(
            duration=models.F('sign_out') - models.F('sign_in')
        )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'center', 'position', 'created_at')
    list_filter = ('center', 'position')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'center__name', 'position')
    ordering = ('user__last_name', 'user__first_name')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'center')
    
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_full_name.short_description = 'Full Name'

    def export_as_csv(self, request, queryset):
        """Export selected attendance records as CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_records.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Child Name',
            'Parent Name',
            'Center',
            'Sign In Time',
            'Sign Out Time',
            'Status',
            'Notes'
        ])
        
        for record in queryset:
            writer.writerow([
                record.child.name,
                record.parent.name,
                record.center.name if record.center else '',
                self.get_today_status(record),
                record.notes
            ])
        
        return response
    export_as_csv.short_description = "Export selected records as CSV"

    def get_today_status(self, obj):
        return obj.get_today_status()
    get_today_status.short_description = 'Status'
