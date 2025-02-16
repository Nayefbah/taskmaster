from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Count,F
from .models import Job, Notes, JobHistory, Attachment
from .forms import JobForm, NoteForm, AttachmentForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.dateparse import parse_date
from .models import STATUS

@login_required
def task_list_view(request):
    tasks = Job.objects.select_related('created_by', 'assigned_to').order_by('-created_at')

    if not request.user.is_superuser:
        tasks = tasks.filter(Q(assigned_to=request.user) | Q(created_by=request.user))

    title_description_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    assigned_to_filter = request.GET.get('assigned_to', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if title_description_query:
        tasks = tasks.filter(Q(title__icontains=title_description_query) | Q(description__icontains=title_description_query))

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if assigned_to_filter:
        if assigned_to_filter == "unassigned":
            tasks = tasks.filter(assigned_to__isnull=True)
        else:
            tasks = tasks.filter(assigned_to__username__icontains=assigned_to_filter)

    if from_date:
        parsed_from_date = parse_date(from_date)
        if parsed_from_date:
            tasks = tasks.filter(created_at__date__gte=parsed_from_date)

    if to_date:
        parsed_to_date = parse_date(to_date)
        if parsed_to_date:
            tasks = tasks.filter(created_at__date__lte=parsed_to_date)

    # Update status to 'In Progress' when the assigned user opens the task list
    for task in tasks:
        if task.assigned_to == request.user and task.status == "Pending":
            task.status = "In Progress"
            task.save()

            JobHistory.objects.create(
                job=task,
                action="Updated",
                performed_by=request.user,
                details=f"Task '{task.title}' status changed to In Progress automatically."
            )

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'query': title_description_query,
        'status_filter': status_filter,
        'assigned_to_filter': assigned_to_filter,
        'from_date': from_date,
        'to_date': to_date,
        'users': User.objects.all(),
        'STATUS': STATUS,
    })

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    if task.assigned_to is not None:
        messages.error(request, "You can only delete unassigned tasks.")
        return redirect('task_list')
    
    JobHistory.objects.create(
        job=task,
        action="Deleted",
        performed_by=request.user,
        details=f"Task '{task.title}' was deleted by {request.user.username}."
    )

    task.attachments.all().delete()
    task.history.all().delete()
    task.delete()

    messages.success(request, "Task deleted successfully.")
    return redirect('task_list')

@login_required
def task_detail_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)
    notes = task.notes.prefetch_related('attachments')
    attachments = task.attachments.all()
    return render(request, 'tasks/task_detail.html', {'task': task, 'notes': notes, 'attachments': attachments})

@login_required
def add_note_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    last_note = Notes.objects.filter(job=task, created_by=request.user).order_by('-created_at').first()

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=last_note)
        attachment_form = AttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            note = form.save(commit=False)
            note.job = task
            note.created_by = request.user
            note.save()

            if 'file' in request.FILES:
                note.attachments.all().delete()
                Attachment.objects.create(note=note, file=request.FILES['file'])

            JobHistory.objects.create(
                job=task,
                action="Updated" if last_note else "Created",
                performed_by=request.user,
                details=f"Note {'updated' if last_note else 'added'}: {note.title}"
            )

            messages.success(request, 'Note updated successfully.' if last_note else 'Note added successfully.')
            return redirect('task_detail', task_id=task.id)
        else:
            messages.error(request, 'Failed to save note. Please check the input.')
    else:
        form = NoteForm(instance=last_note)
        attachment_form = AttachmentForm()

    return render(request, 'tasks/add_note.html', {
        'form': form,
        'attachment_form': attachment_form,
        'task': task,
        'last_note': last_note,
    })

@login_required
def delete_last_note(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    last_note = Notes.objects.filter(job=task, created_by=request.user).order_by('-created_at').first()

    if last_note:
        JobHistory.objects.create(
            job=task,
            action="Deleted",
            performed_by=request.user,
            details=f"Note '{last_note.title}' was deleted by {request.user.username}."
        )

        last_note.delete()
        messages.success(request, "Your last note was deleted successfully.")
    else:
        messages.error(request, "You have no note to delete.")

    return redirect('task_detail', task_id=task.id)


@login_required
def complete_task_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    if not request.user.is_superuser and task.assigned_to != request.user:
        return HttpResponseForbidden("You do not have permission to complete this task.")

    if request.method == 'POST':
        task.status = 'Completed'
        task.save()

        JobHistory.objects.create(
            job=task,
            action='Completed',
            performed_by=request.user,
            details='Task was marked as completed.'
        )

        messages.success(request, 'Task marked as completed.')
        return redirect('task_detail', task_id=task.id)

    return render(request, 'tasks/complete_task.html', {'task': task})


@login_required
def transfer_task_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    if task.status == 'Completed':
        return HttpResponseForbidden("Cannot transfer a completed task.")

    if request.method == 'POST':
        new_assignee_id = request.POST.get('assigned_to')

        if task.assigned_to and task.assigned_to.id == int(new_assignee_id):
            messages.error(request, "You cannot transfer the task to yourself.")
            return redirect('task_detail', task_id=task.id)

        try:
            new_assignee = User.objects.get(id=new_assignee_id)
            previous_assignee = task.assigned_to

            task.assigned_to = new_assignee
            task.status = 'Pending'
            task.save()

            JobHistory.objects.create(
                job=task,
                action='Transferred',
                performed_by=request.user,
                details=f'Task transferred from {previous_assignee.username if previous_assignee else "Unassigned"} to {new_assignee.username}.'
            )

            JobHistory.objects.create(
                job=task,
                action='Received',
                performed_by=new_assignee,
                details=f'Task received by {new_assignee.username} from {previous_assignee.username if previous_assignee else "Unassigned"}.'
            )

            messages.success(request, f"Task transferred to {new_assignee.username}.")
            return redirect('task_detail', task_id=task.id)
        except User.DoesNotExist:
            messages.error(request, "Invalid user selected.")

    users = User.objects.exclude(id=task.assigned_to.id) if task.assigned_to else User.objects.all()
    return render(request, 'tasks/transfer_task.html', {'task': task, 'users': users})

@login_required
def create_task_view(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        attachment_form = AttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()

            JobHistory.objects.create(
                job=job,
                action="Created",
                performed_by=request.user,
                details=f"Task '{job.title}' was created by {request.user.username}."
            )

            if request.FILES.get('file'):
                attachment = Attachment(task=job, file=request.FILES['file'])
                attachment.save()

            messages.success(request, 'Task created successfully.')
            return redirect('task_list')
        else:
            messages.error(request, "There was an error creating the task. Please check the form inputs.")

    else:
        form = JobForm()
        attachment_form = AttachmentForm()

    return render(request, 'tasks/create_task.html', {
        'form': form,
        'attachment_form': attachment_form,
        'page_title': 'Create Task',
        'submit_button_text': 'Save'
    })


@login_required
def edit_task(request, task_id):
    job = get_object_or_404(Job, id=task_id)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        attachment_form = AttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            old_status = job.status
            old_due_date = job.due_date
            old_assigned_to = job.assigned_to 

            form.save()

            changes = []
            if form.cleaned_data.get('status') != old_status:
                changes.append(f"Status changed to {form.cleaned_data['status']}")
            if form.cleaned_data.get('due_date') != old_due_date:
                changes.append(f"Due date updated to {form.cleaned_data['due_date']}")
            if 'assigned_to' in form.cleaned_data and form.cleaned_data['assigned_to'] != old_assigned_to:
                assigned_to_user = form.cleaned_data['assigned_to']
                assigned_to_name = assigned_to_user.username if assigned_to_user else "Unassigned"
                changes.append(f"Assigned to {assigned_to_name}")

            if changes:
                JobHistory.objects.create(
                    job=job,
                    action="Updated",
                    performed_by=request.user,
                    details=", ".join(changes)
                )

            if 'file' in request.FILES:
                job.attachments.all().delete()
                Attachment.objects.create(task=job, file=request.FILES['file'])

            messages.success(request, 'Task updated successfully.')
            return redirect('task_detail', task_id=job.id)
    else:
        form = JobForm(instance=job)
        attachment_form = AttachmentForm()

    return render(request, 'tasks/edit_task.html', {
        'form': form,
        'attachment_form': attachment_form,
        'task': job,
        'page_title': 'Edit Task',
        'submit_button_text': 'Save Changes'
    })


@login_required
def task_history_view(request, task_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to view task history.")

    task = get_object_or_404(Job, id=task_id)
    history = task.history.all().order_by('-timestamp')
    return render(request, 'tasks/task_history.html', {'task': task, 'history': history})


@login_required
def change_task_status_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    if task.status == 'Completed':
        return HttpResponseForbidden("Cannot change status of a completed task.")

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Job.STATUS).keys():
            task.status = new_status
            task.save()
            JobHistory.objects.create(
                job=task,
                action='Status Changed',
                performed_by=request.user,
                details=f'Task status changed to {new_status}.'
            )
            messages.success(request, "Task status updated.")
            return redirect('task_detail', task_id=task.id)
        else:
            messages.error(request, "Invalid status selected.")

    return render(request, 'tasks/change_status.html', {'task': task})


@login_required
@staff_member_required
def task_statistics_view(request):
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    parsed_from_date = parse_date(from_date) if from_date else None
    parsed_to_date = parse_date(to_date) if to_date else None

    task_filter = Q()
    
    if parsed_from_date:
        task_filter &= Q(created_at__date__gte=parsed_from_date)
    
    if parsed_to_date:
        task_filter &= Q(created_at__date__lte=parsed_to_date)

    created_tasks = Job.objects.filter(task_filter).count() 
    pending_tasks = Job.objects.filter(task_filter, status='Pending').count()
    in_progress_tasks = Job.objects.filter(task_filter, status='In Progress').count()
    completed_tasks = Job.objects.filter(task_filter, status='Completed').count()
    total_tasks = created_tasks 

    employee_stats = User.objects.annotate(
        jobs_created=Count('created_jobs', filter=task_filter),
        pending_tasks=Count('assigned_jobs', filter=task_filter & Q(assigned_jobs__status='Pending')),
        in_progress_tasks=Count('assigned_jobs', filter=task_filter & Q(assigned_jobs__status='In Progress')),
        completed_tasks=Count('assigned_jobs', filter=task_filter & Q(assigned_jobs__status='Completed')),
        total_tasks=Count('assigned_jobs', filter=task_filter)  # ✅ Total
    ).order_by('-total_tasks')

    return render(request, 'tasks/task_statistics.html', {
        'created_tasks': created_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'employee_stats': employee_stats,
        'from_date': from_date,
        'to_date': to_date
    })


@login_required
@staff_member_required
def admin_history_view(request):
    username = request.GET.get('username', '')
    job_title = request.GET.get('job_title', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    parsed_from_date = parse_date(from_date) if from_date else None
    parsed_to_date = parse_date(to_date) if to_date else None

    history_query = JobHistory.objects.select_related('job', 'performed_by').order_by('-timestamp')

    if username:
        history_query = history_query.filter(performed_by__username__icontains=username)

    if job_title:
        history_query = history_query.filter(job__title__icontains=job_title)

    if parsed_from_date:
        history_query = history_query.filter(timestamp__date__gte=parsed_from_date)

    if parsed_to_date:
        history_query = history_query.filter(timestamp__date__lte=parsed_to_date)

    users = User.objects.all()
    jobs = Job.objects.all()

    return render(request, 'tasks/admin_history.html', {
        'history': history_query,
        'users': users,
        'jobs': jobs,
        'username': username,
        'job_title': job_title,
        'from_date': from_date,
        'to_date': to_date,
    })

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # ✅ The user is created but has NO GROUP, making them inactive for now
            messages.success(request, "Account created successfully! Waiting for admin approval.")
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "tasks/signup.html", {"form": form})

def home_view(request):
    return render(request, 'home.html')
