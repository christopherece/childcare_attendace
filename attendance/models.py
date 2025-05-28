from django.db import models
from django.utils import timezone

class Parent(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Child(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Attendance(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.child.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
