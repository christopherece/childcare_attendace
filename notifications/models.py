from django.db import models
from django.utils import timezone
from django.utils import timezone
from attendance.models import Child, Parent
from datetime import timedelta

NOTIFICATION_TYPES = [
    ('late_sign_in', 'Late Sign In'),
    ('late_sign_out', 'Late Sign Out'),
    ('general', 'General Notification'),
]

class Notification(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='notifications')
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.notification_type} - {self.child.name}"
    
    @classmethod
    def create_late_notification(cls, child, notification_type, message):
        """Create a notification for late sign-in/sign-out"""
        parent = child.parent
        return cls.objects.create(
            child=child,
            parent=parent,
            notification_type=notification_type,
            message=message
        )
    
    @classmethod
    def mark_as_read(cls, notification_ids):
        """Mark multiple notifications as read"""
        cls.objects.filter(id__in=notification_ids).update(is_read=True)
    
    @classmethod
    def mark_as_unread(cls, notification_ids):
        """Mark multiple notifications as unread"""
        cls.objects.filter(id__in=notification_ids).update(is_read=False)
    
    @classmethod
    def get_recent_notifications(cls, days=7):
        """Get recent notifications within the last X days"""
        return cls.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=days)
        ).order_by('-timestamp')
