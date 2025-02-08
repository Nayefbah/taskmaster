from django.db import models
from django.contrib.auth.models import User



STATUS=(
('P', 'pending'),('I','In Progress'),('C','Completed')
)

ACTION=(('Cr', 'Created'),
        ('Up', 'Updated'),
        ('Tr', 'Transferred'),
        ('Co', 'Completed'),)
class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS,default=STATUS[0][0])
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_jobs')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class Notes(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    editable = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class JobHistory(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    action = models.CharField(max_length=2, choices=ACTION,default=ACTION[0][0])
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)  # Optional details about the action

    def __str__(self):
        return f"{self.job.title} - {self.action} by {self.performed_by.username}"
