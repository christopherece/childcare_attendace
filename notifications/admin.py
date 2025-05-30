from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('child', 'parent', 'notification_type', 'message', 'timestamp', 'is_read')
    list_filter = ('notification_type', 'is_read', 'timestamp')
    search_fields = ('child__name', 'parent__name', 'message')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        """Prevent adding notifications through admin interface"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting notifications through admin interface"""
        return False
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        queryset.update(is_read=True)
        self.message_user(request, f"Successfully marked {queryset.count()} notifications as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        queryset.update(is_read=False)
        self.message_user(request, f"Successfully marked {queryset.count()} notifications as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"
    
    actions = [mark_as_read, mark_as_unread]
