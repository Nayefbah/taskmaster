from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

STATUS = (
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    ('Completed', 'Completed')
)

ACTION = (
    ('Created', 'Created'),
    ('Updated', 'Updated'),
    ('Transferred', 'Transferred'),
    ('Completed', 'Completed')
)

class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS, default='Pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_jobs')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def update_status(self, new_status, user):
        """Update status and create a history record."""
        self.status = new_status
        self.save()
        JobHistory.objects.create(
            job=self,
            action=f"Status changed to {new_status}",
            performed_by=user,
            details=f"Task status updated to {new_status} by {user.username}."
        )


class Notes(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    editable = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class JobHistory(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION, default='Created')
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.job.title} - {self.action} by {self.performed_by.username}"
    

class Attachment(models.Model):
    task = models.ForeignKey('Job', on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    note = models.ForeignKey('Notes', on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    file = models.FileField(upload_to='static/attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.task and not self.note:
            raise ValidationError("Attachment must be related to either a task or a note.")
        if self.task and self.note:
            raise ValidationError("Attachment cannot be related to both a task and a note.")

    def __str__(self):
        return f"Attachment for {self.task or self.note}"