from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Job, Notes, JobHistory
from .forms import JobForm, NoteForm

# Task List View
@login_required
def task_list_view(request):
    tasks = Job.objects.all() if request.user.is_superuser else Job.objects.filter(assigned_to=request.user)
    return render(request, 'tasks/task_list.html', {'tasks': tasks})


# Task Detail View
@login_required
def task_detail_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)
    notes = task.notes_set.all()
    return render(request, 'tasks/task_detail.html', {'task': task, 'notes': notes})


# Add Note View
@login_required
def add_note_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.job = task
            note.created_by = request.user
            note.save()
            messages.success(request, "Note added successfully.")
            return redirect('task_detail', task_id=task.id)
    else:
        form = NoteForm()

    return render(request, 'tasks/add_note.html', {'form': form, 'task': task})


# Task History View
@login_required
def task_history_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)
    history = task.jobhistory_set.all().order_by('-timestamp')
    return render(request, 'tasks/task_history.html', {'task': task, 'history': history})


# Create Task View
@login_required
def create_task_view(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            JobHistory.objects.create(
                job=job,
                action='Created',
                performed_by=request.user,
                details='Task was created.'
            )
            messages.success(request, "Task created successfully.")
            return redirect('task_list')
    else:
        form = JobForm()

    return render(request, 'tasks/create_task.html', {'form': form})


# Edit Task View
@login_required
def edit_task_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            JobHistory.objects.create(
                job=task,
                action='Updated',
                performed_by=request.user,
                details='Task was updated.'
            )
            messages.success(request, "Task updated successfully.")
            return redirect('task_detail', task_id=task.id)
    else:
        form = JobForm(instance=task)

    return render(request, 'tasks/edit_task.html', {'form': form, 'task': task})


# Change Task Status View
@login_required
def change_task_status_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
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

    return render(request, 'tasks/change_status.html', {'task': task})


# Transfer Task View
@login_required
def transfer_task_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)

    if request.method == 'POST':
        new_assignee_id = request.POST.get('assigned_to')
        try:
            new_assignee = User.objects.get(id=new_assignee_id)
            task.assigned_to = new_assignee
            task.save()
            JobHistory.objects.create(
                job=task,
                action='Transferred',
                performed_by=request.user,
                details=f'Task was transferred to {new_assignee.username}.'
            )
            messages.success(request, f"Task transferred to {new_assignee.username}.")
            return redirect('task_detail', task_id=task.id)
        except User.DoesNotExist:
            messages.error(request, "Invalid user selected.")

    return render(request, 'tasks/transfer_task.html', {'task': task})


# Home View
def home_view(request):
    return render(request, 'home.html')
