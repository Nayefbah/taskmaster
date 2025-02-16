# Generated by Django 5.1.6 on 2025-02-10 15:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_app', '0003_alter_job_assigned_to_alter_job_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='attachments/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='my_app.notes')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='my_app.job')),
            ],
        ),
    ]
