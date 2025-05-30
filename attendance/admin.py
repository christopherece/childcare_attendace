from django.contrib import admin
from django.db import models
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
    list_display = ('child', 'parent', 'center', 'timestamp', 'action_type', 'attendance_status', 'late', 'late_reason', 'created_at')
    list_filter = (
        'timestamp', 
        'child__parent', 
        'center', 
        'action_type',
        'late',
        'late_reason'
    )
    search_fields = ('child__name', 'parent__name', 'center__name', 'notes')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('created_at',)
    actions = ['export_as_csv']

    def attendance_status(self, obj):
        return obj.get_current_status(obj.child)
    attendance_status.short_description = 'Status'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Add annotations for better filtering
        return queryset.annotate(
            duration=models.Subquery(
                Attendance.objects.filter(
                    child=models.OuterRef('child'),
                    timestamp__date=models.OuterRef('timestamp__date'),
                    action_type='sign_out'
                ).annotate(
                    sign_in_time=models.Subquery(
                        Attendance.objects.filter(
                            child=models.OuterRef('child'),
                            timestamp__date=models.OuterRef('timestamp__date'),
                            action_type='sign_in'
                        ).values('timestamp')[:1]
                    )
                ).annotate(
                    duration=models.F('timestamp') - models.F('sign_in_time')
                ).values('duration')[:1]
            )
        )

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
            'Timestamp',
            'Action Type',
            'Status',
            'Late',
            'Late Reason',
            'Notes'
        ])
        
        for record in queryset:
            writer.writerow([
                record.child.name,
                record.parent.name,
                record.center.name if record.center else '',
                record.timestamp,
                record.action_type,
                self.attendance_status(record),
                record.late,
                record.late_reason,
                record.notes
            ])
        
        return response
    export_as_csv.short_description = "Export selected records as CSV"
    list_filter = ('timestamp', 'child__parent', 'center')
    search_fields = ('child__name', 'parent__name', 'center__name')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('created_at',)
