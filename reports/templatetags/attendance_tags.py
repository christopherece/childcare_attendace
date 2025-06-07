from django import template
from django.utils import timezone
from attendance.models import Attendance

register = template.Library()

@register.filter
def get_sign_in_time(date_attendances, child_id):
    """Get the sign-in time for a child from the date_attendances dictionary"""
    attendance = date_attendances.get(child_id)
    if attendance and attendance.sign_in:
        return timezone.localtime(attendance.sign_in).strftime("%H:%M")
    return "-"

@register.filter
def get_today_attendance(child, date):
    """Get the attendance record for a child on a specific date"""
    if not date:
        date = timezone.now().date()
    return Attendance.objects.filter(
        child=child,
        sign_in__date=date
    ).first()
