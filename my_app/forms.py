from django import forms
from .models import Job,Notes

class JobForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control' 
        }),
        required=False
    )

    class Meta:
        model = Job
        fields = ['title', 'description', 'due_date', 'status', 'assigned_to']


class NoteForm(forms.ModelForm):
    class Meta:
        model = Notes
        fields = ['title', 'description']