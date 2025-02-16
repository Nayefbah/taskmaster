from django import forms
from .models import Job, Notes, Attachment
from datetime import datetime 
from django.utils.dateparse import parse_datetime

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'status', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.TextInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'})
        }

    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')

        if isinstance(due_date, datetime):
            return due_date

        if due_date:
            parsed_due_date = parse_datetime(due_date)
            if not parsed_due_date:
                raise forms.ValidationError("Invalid due date format.")
            return parsed_due_date

        raise forms.ValidationError("Due date is required.")

class NoteForm(forms.ModelForm):
    class Meta:
        model = Notes
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AttachmentForm(forms.ModelForm):
    file = forms.FileField(
        required=False,  # ✅ Makes file upload optional
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Attachment
        fields = ['file']
