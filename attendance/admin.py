from django.contrib import admin
from django.db import models
from .models import Child, Parent, Attendance, Center, Teacher, Room

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
    search_fields = ('child__name', 'parent__name', 'center__name', 'notes')
    ordering = ('-sign_in',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Add annotations for better filtering
        return queryset.annotate(
            duration=models.F('sign_out') - models.F('sign_in')
        )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'center', 'position', 'phone', 'email', 'created_at')
    list_filter = ('center', 'position')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'center__name', 'position')
    ordering = ('user__last_name', 'user__first_name')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'center')
    
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_full_name.short_description = 'Full Name'

    def export_as_pdf(self, request, queryset):
        """Export selected attendance records as PDF"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from django.http import HttpResponse
        from datetime import datetime
        
        # Create the HTTP response with PDF headers
        response = HttpResponse(content_type='application/pdf')
        filename = f"attendance_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create the PDF object
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title = Paragraph('Attendance Records', styles['Title'])
        elements.append(title)
        
        # Create table data
        data = [
            ['Child Name', 'Parent Name', 'Center', 'Sign In Time', 'Sign Out Time', 'Status', 'Notes']
        ]
        
        for record in queryset:
            data.append([
                record.child.name,
                record.parent.name,
                record.center.name if record.center else '',
                record.sign_in.strftime('%Y-%m-%d %H:%M:%S') if record.sign_in else '',
                record.sign_out.strftime('%Y-%m-%d %H:%M:%S') if record.sign_out else '',
                self.get_today_status(record),
                record.notes
            ])
        
        # Create table
        table = Table(data)
        
        # Add table style
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 14),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ])
        table.setStyle(style)
        elements.append(table)
        
        # Build the PDF
        doc.build(elements)
        
        return response
    export_as_pdf.short_description = "Export selected records as PDF"

    def get_today_status(self, obj):
        return obj.get_today_status()
    get_today_status.short_description = 'Status'

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'center', 'capacity', 'age_range', 'created_at')
    list_filter = ('center', 'capacity', 'age_range')
    search_fields = ('name', 'center__name', 'age_range', 'description')
    ordering = ('center', 'name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('center')
