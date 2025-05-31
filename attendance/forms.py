from django import forms
from .models import Teacher

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['position', 'profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['position'].widget.attrs.update({'placeholder': 'e.g., Lead Teacher, Assistant Teacher'})
