from django import forms
from .models import Job, Notes


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'status', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_due_date'}),
        }

class NoteForm(forms.ModelForm):
    class Meta:
        model = Notes
        fields = ['title', 'description']