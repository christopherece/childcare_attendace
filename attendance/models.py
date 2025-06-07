from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User

class Center(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    capacity = models.IntegerField()
    opening_time = models.TimeField(default='08:30:00')  # Default opening time is 8:30 AM
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Room(models.Model):
    name = models.CharField(max_length=100)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='rooms')
    capacity = models.IntegerField()
    age_range = models.CharField(max_length=50, help_text="e.g., '2-3 years', '3-5 years'")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('center', 'name')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} at {self.center.name}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True, related_name='teachers')
    rooms = models.ManyToManyField(Room, blank=True, related_name='teachers')
    position = models.CharField(max_length=100, default='Teacher')
    profile_picture = models.ImageField(upload_to='static/images/teachers/', blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.user.get_full_name()} - {self.position}'
    
    class Meta:
        ordering = ['-created_at']

class Parent(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Child(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    )
    emergency_contact = models.CharField(max_length=100, default='Emergency Contact')
    emergency_phone = models.CharField(max_length=30, default='')
    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='static/images/children/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
            return self.profile_picture.url
        return '/static/images/user-default.png'

class Attendance(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True)
    sign_in = models.DateTimeField(null=True, blank=True)  # Time of sign-in
    sign_out = models.DateTimeField(null=True, blank=True)  # Time of sign-out
    notes = models.TextField(blank=True, null=True)
    late = models.BooleanField(default=False)
    late_reason = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        ordering = ['-sign_in', '-sign_out']
        constraints = [
            # Ensure active sign-ins are unique
            models.UniqueConstraint(
                fields=['child', 'sign_in'],
                condition=models.Q(sign_out__isnull=True),
                name='unique_active_sign_in'
            )
        ]

    def clean(self):
        super().clean()
        
        if self.sign_in:
            # Check if there's an existing sign-in for today that hasn't been signed out
            today = self.sign_in.date()
            existing = Attendance.objects.filter(
                child=self.child,
                sign_in__date=today,
                sign_out__isnull=True
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError('Child is already signed in today')

            # Check if sign-out is before sign-in
            if self.sign_out and self.sign_out <= self.sign_in:
                raise ValidationError('Sign-out time must be after sign-in time')

            # Check if sign-out is on the same day as sign-in
            if self.sign_out and self.sign_out.date() != self.sign_in.date():
                raise ValidationError('Sign-out must be on the same day as sign-in')

    def save(self, *args, **kwargs):
        """Override save to ensure validation is run"""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.center:
            return f"{self.child.name} signed in at {self.center.name} on {self.sign_in.strftime('%Y-%m-%d %H:%M:%S')}"
        return f"{self.child.name} signed in on {self.sign_in.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @classmethod
    def check_existing_record(cls, child):
        """Check if there's an existing record for this child today"""
        today = timezone.now().astimezone(NZ_TIMEZONE).date()
        return cls.objects.filter(
            child=child,
            sign_in__date=today,
            sign_out__isnull=True  # Only count active sign-ins
        ).exists()

    @classmethod
    def get_today_record(cls, child):
        """Get today's attendance record for a child"""
        today = timezone.now().astimezone(NZ_TIMEZONE).date()
        return cls.objects.filter(
            child=child,
            sign_in__date=today,
            sign_out__isnull=True  # Get the active sign-in
        ).first()

    @classmethod
    def validate_sign_in(cls, child):
        """Validate if a child can sign in today"""
        if cls.check_existing_record(child):
            raise ValidationError('Child is already signed in today')
        return True

    @classmethod
    def get_daily_attendance(cls, child, date):
        """Get all attendance records for a child on a specific date"""
        return cls.objects.filter(
            child=child,
            sign_in__date=date
        ).order_by('-sign_in')



    @classmethod
    def validate_sign_in(cls, child):
        """Validate if a child can sign in today"""
        if cls.check_existing_record(child):
            raise ValidationError('Child is already signed in today')
        return True

    def clean(self):
        """Run validation checks"""
        super().clean()
        
        if not self.pk:  # Only check on creation
            if not self.sign_in:
                raise ValidationError('Sign-in time is required')
            
            # Ensure there's no existing sign-in for today
            if self.child and self.sign_in:
                self.validate_sign_in(self.child)
            
            # Set parent and center based on child
            if self.child:
                self.parent = self.child.parent
                self.center = self.child.center
        
        # Validate sign-out time
        if self.sign_out and self.sign_in:
            if self.sign_out <= self.sign_in:
                raise ValidationError('Sign-out time must be after sign-in time')
            if self.sign_out.date() != self.sign_in.date():
                raise ValidationError('Sign-out must be on the same day as sign-in')
    
    @classmethod
    def get_today_status(cls, child):
        """Get the attendance status for today"""
        today = timezone.now().date()
        record = cls.objects.filter(
            child=child,
            sign_in__date=today
        ).first()
        
        if not record:
            return 'not_signed_in'
        
        if record.sign_out:
            return 'signed_out'
        return 'signed_in'
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is run"""
        self.clean()
        super().save(*args, **kwargs)
    
    def clean(self):
        """Run validation checks"""
        if not self.pk:  # Only check on creation
            if not self.sign_in:
                raise ValidationError('Sign-in time is required')
            if self.sign_out and self.sign_out <= self.sign_in:
                raise ValidationError('Sign-out time must be after sign-in time')
        super().clean()
    
    @classmethod
    def get_daily_attendance(cls, child, date):
        """Get all attendance records for a child on a specific date"""
        return cls.objects.filter(
            child=child,
            sign_in__date=date
        ).order_by('sign_in')
    
    @classmethod
    def get_current_status(cls, child):
        """Get the current attendance status of a child"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        if not records.exists():
            return 'Not signed in'
        
        last_record = records.last()
        if last_record.sign_out is None:
            return 'Signed in'
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
            if record.sign_in and not record.sign_out:
                sign_in = record.sign_in
            elif record.sign_out and sign_in:
                total_duration += record.sign_out - sign_in
                sign_in = None
        
        return total_duration
    
    @classmethod
    def is_signed_in(cls, child):
        """Check if a child is currently signed in"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        return len(records) % 2 != 0 and records.last().sign_out is None
    
    @classmethod
    def can_sign_in(cls, child):
        """Check if a child can be signed in today"""
        # Always allow sign-in at the start of the day
        return True
    
    @classmethod
    def can_sign_out(cls, child):
        """Check if a child can be signed out today"""
        today = timezone.now().date()
        records = cls.get_daily_attendance(child, today)
        # Can sign out if there's at least one record with sign_in and no sign_out
        return records.filter(sign_in__isnull=False, sign_out__isnull=True).exists()
    
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
