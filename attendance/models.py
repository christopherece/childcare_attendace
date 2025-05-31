from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

class Center(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    capacity = models.IntegerField()
    opening_time = models.TimeField(default='08:30:00')  # Default opening time is 8:30 AM
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Parent(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Child(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    )
    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to='static/images/child_pix/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.center:
            return f"{self.name} at {self.center.name}"
        return self.name
    
    def get_age(self):
        """Calculate the child's age in years"""
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age
    
    def get_profile_picture_url(self):
        """Return the URL of the profile picture or a default image"""
        if self.profile_picture:
            # Get the relative path from the profile_picture field
            relative_path = self.profile_picture.name
            # Return the correct static URL
            return f"/static/images/child_pix/{relative_path.split('/')[-1]}"
        return '/static/images/child_pix/user-default.png'

class Attendance(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)  # Automatically set to current time when record is created
    prevent_sign_in_until_tomorrow = models.BooleanField(default=False)  # Flag to prevent sign-in until tomorrow
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set timestamp to current time if not provided
        if 'timestamp' not in kwargs:
            self.timestamp = timezone.now()
    prevent_sign_in_until_tomorrow = models.BooleanField(default=False)  # Flag to prevent sign-in until tomorrow
    
    def save(self, *args, **kwargs):
        """Ensure timestamp is set to current time before saving"""
        # Always set timestamp to current time
        self.timestamp = timezone.now()
        
        # For sign-out, set prevent_sign_in_until_tomorrow flag
        if self.action_type == 'sign_out':
            self.prevent_sign_in_until_tomorrow = True
            
        super().save(*args, **kwargs)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    action_type = models.CharField(max_length=10, choices=[('sign_in', 'Sign In'), ('sign_out', 'Sign Out')], default='sign_in')
    notes = models.TextField(blank=True, null=True)
    late = models.BooleanField(default=False)
    late_reason = models.CharField(max_length=100, blank=True, null=True)

    @classmethod
    def check_existing_record(cls, child, action_type):
        """Check if there's an existing record for this child and action type today"""
        today = timezone.now().date()
        return cls.objects.filter(
            child=child,
            timestamp__date=today,
            action_type=action_type
        ).exists()

    @classmethod
    def get_today_status(cls, child):
        """Get the attendance status for today"""
        today = timezone.now().date()
        records = cls.objects.filter(
            child=child,
            timestamp__date=today
        ).order_by('-timestamp')
        
        if not records.exists():
            return 'not_signed_in'
            
        last_record = records.first()
        return 'signed_in' if last_record.action_type == 'sign_in' else 'signed_out'

    def save(self, *args, **kwargs):
        """Check for existing record before saving"""
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Run validation checks"""
        if not self.pk:  # Only check on creation
            if self.action_type == 'sign_in':
                if self.check_existing_record(self.child, 'sign_in'):
                    raise ValidationError('Child is already signed in today')
                if self.prevent_sign_in_until_tomorrow:
                    raise ValidationError('Cannot sign in until tomorrow')
            else:  # sign_out
                if not self.check_existing_record(self.child, 'sign_in'):
                    raise ValidationError('Child is not signed in today')
                if self.check_existing_record(self.child, 'sign_out'):
                    raise ValidationError('Child is already signed out today')
        
        # Ensure timestamp is set to current time
        if not self.timestamp:
            self.timestamp = timezone.now()
        
        super().clean()
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        if self.center:
            return f"{self.child.name} {self.action_type} at {self.center.name} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        return f"{self.child.name} {self.action_type} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def get_daily_attendance(cls, child, date):
        """Get all attendance records for a child on a specific date"""
        return cls.objects.filter(
            child=child,
            timestamp__date=date
        ).order_by('timestamp')

    @classmethod
    def get_current_status(cls, child):
        """Get the current attendance status of a child"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        if not records.exists():
            return 'Not signed in'
        
        last_record = records.last()
        if last_record.action_type == 'sign_in':
            return 'Signed in'
        else:
            return 'Signed out'

    @classmethod
    def get_daily_duration(cls, child, date):
        """Calculate the total duration a child was signed in on a specific date"""
        records = cls.get_daily_attendance(child, date)
        if not records.exists():
            return timedelta(0)
            
        total_duration = timedelta(0)
        sign_in = None
        
        for record in records:
            if record.action_type == 'sign_in':
                sign_in = record.timestamp
            else:  # sign_out
                if sign_in:
                    total_duration += record.timestamp - sign_in
                    sign_in = None
        
        return total_duration

    @classmethod
    def is_signed_in(cls, child):
        """Check if a child is currently signed in"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        return len(records) % 2 != 0 and records.last().action_type == 'sign_in'

    @classmethod
    def can_sign_in(cls, child):
        """Check if a child can be signed in today"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        # Can sign in if there are no records or if the last record was a sign-out
        return len(records) == 0 or (len(records) % 2 == 0)

    @classmethod
    def can_sign_out(cls, child):
        """Check if a child can be signed out today"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        # Can sign out if there is at least one sign-in record and the last record is a sign-in
        return len(records) > 0 and (len(records) % 2 != 0)

    @classmethod
    def check_late_sign_in(cls, child, timestamp):
        """Check if a sign-in is late based on center's operating hours"""
        if not child.center:
            return False
            
        # Define center operating hours (example: 8:00 AM to 6:00 PM)
        start_hour = 8
        end_hour = 18
        
        # Consider sign-in late if after 9:00 AM
        late_hour = 9
        
        if timestamp.hour >= late_hour:
            return True
        return False

    @classmethod
    def check_late_sign_out(cls, child, timestamp):
        """Check if a sign-out is late based on center's operating hours"""
        if not child.center:
            return False
            
        # Define center operating hours (example: 8:00 AM to 6:00 PM)
        end_hour = 18
        
        # Consider sign-out late if after 6:00 PM
        if timestamp.hour >= end_hour:
            return True
        return False

    def save(self, *args, **kwargs):
        """Override save method to check for late sign-ins/sign-outs"""
        if self.action_type == 'sign_in':
            self.late = self.check_late_sign_in(self.child, self.timestamp)
            if self.late:
                self.late_reason = 'After operating hours'
        else:  # sign_out
            self.late = self.check_late_sign_out(self.child, self.timestamp)
            if self.late:
                self.late_reason = 'After closing time'
                
        super().save(*args, **kwargs)

    @classmethod
    def get_attendance_stats(cls, child, start_date, end_date):
        """Get attendance statistics for a child over a date range"""
        records = cls.objects.filter(
            child=child,
            timestamp__date__range=[start_date, end_date]
        )
        
        stats = {
            'total_days': (end_date - start_date).days + 1,
            'total_sign_ins': records.filter(action_type='sign_in').count(),
            'total_sign_outs': records.filter(action_type='sign_out').count(),
            'late_sign_ins': records.filter(action_type='sign_in', late=True).count(),
            'late_sign_outs': records.filter(action_type='sign_out', late=True).count(),
            'average_daily_duration': timedelta(0)
        }
        
        # Calculate average daily duration
        total_duration = timedelta(0)
        for record in records:
            if record.action_type == 'sign_in':
                sign_in = record.timestamp
                try:
                    sign_out = records.get(
                        child=child,
                        timestamp__date=record.timestamp.date(),
                        action_type='sign_out'
                    )
                    total_duration += sign_out.timestamp - sign_in
                except cls.DoesNotExist:
                    pass
        
        if stats['total_sign_ins'] > 0:
            stats['average_daily_duration'] = total_duration / stats['total_sign_ins']
        
        return stats

    def __str__(self):
        if self.center:
            return f"{self.child.name} {self.action_type} at {self.center.name} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        return f"{self.child.name} {self.action_type} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def get_daily_attendance(cls, child, date):
        """Get all attendance records for a child on a specific date"""
        return cls.objects.filter(
            child=child,
            timestamp__date=date
        ).order_by('timestamp')

    @classmethod
    def get_current_status(cls, child):
        """Get the current attendance status of a child"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        if not records.exists():
            return 'Not signed in'
        
        last_record = records.last()
        if last_record.action_type == 'sign_in':
            return 'Signed in'
        else:
            return 'Signed out'

    @classmethod
    def get_daily_duration(cls, child, date):
        """Calculate the total duration a child was signed in on a specific date"""
        records = cls.get_daily_attendance(child, date)
        if not records.exists():
            return timedelta(0)
            
        total_duration = timedelta(0)
        sign_in = None
        
        for record in records:
            if record.action_type == 'sign_in':
                sign_in = record.timestamp
            else:  # sign_out
                if sign_in:
                    total_duration += record.timestamp - sign_in
                    sign_in = None
        
        return total_duration

    @classmethod
    def is_signed_in(cls, child):
        """Check if a child is currently signed in"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        return len(records) % 2 != 0 and records.last().action_type == 'sign_in'

    @classmethod
    def can_sign_in(cls, child):
        """Check if a child can be signed in today"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        # Can sign in if there are no records or if the last record was a sign-out
        return len(records) == 0 or (len(records) % 2 == 0)

    @classmethod
    def can_sign_out(cls, child):
        """Check if a child can be signed out today"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        # Can sign out if there is at least one sign-in record and the last record is a sign-in
        return len(records) > 0 and (len(records) % 2 != 0)

    def __str__(self):
        if self.center:
            return f"{self.child.name} {self.action_type} at {self.center.name} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        return f"{self.child.name} {self.action_type} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def get_daily_attendance(cls, child, date):
        """Get all attendance records for a child on a specific date"""
        return cls.objects.filter(
            child=child,
            timestamp__date=date
        ).order_by('timestamp')


