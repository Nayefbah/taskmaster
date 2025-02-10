from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import Job, Notes, JobHistory
from .forms import JobForm, NoteForm

@login_required
def task_list_view(request):
    tasks = Job.objects.all() if request.user.is_superuser else Job.objects.filter(
        Q(assigned_to=request.user) | Q(created_by=request.user)
    )
    return render(request, 'tasks/task_list.html', {'tasks': tasks})


@login_required
def task_detail_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)
    notes = task.notes.all()

    if not request.user.is_superuser and task.status == 'Pending' and task.assigned_to == request.user:
        task.status = 'In Progress'
        task.save()
        JobHistory.objects.create(
            job=task,
            action='Status Changed',
            performed_by=request.user,
            details='Task status changed to In Progress on view.'
        )

    return render(request, 'tasks/task_detail.html', {'task': task, 'notes': notes})


@login_required
def add_note_view(request, task_id):
    task = get_object_or_404(Job, id=task_id)
    last_note = task.notes.last()

    if last_note and last_note.editable and last_note.created_by == request.user:
        if request.method == 'POST':
            form = NoteForm(request.POST, instance=last_note)
            if form.is_valid():
                form.save()
                messages.success(request, 'Note updated successfully.')
                return redirect('task_detail', task_id=task.id)
        else:
            form = NoteForm(instance=last_note)
    else:
        if request.method == 'POST':
            form = NoteForm(request.POST)
            if form.is_valid():
                note = form.save(commit=False)
                note.job = task
                note.created_by = request.user
                note.save()
                JobHistory.objects.create(
                    job=task,
                    action='Note Added',
                    performed_by=request.user,
                    details=f'Note "{note.title}" added.'
                )
                messages.success(request, 'Note added successfully.')
                return redirect('task_detail', task_id=task.id)
        else:
            form = NoteForm()

    return render(request, 'tasks/add_note.html', {'form': form, 'task': task})


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

    if request.method == 'POST':
        new_assignee_id = request.POST.get('assigned_to')
        try:
            new_assignee = User.objects.get(id=new_assignee_id)
            task.assigned_to = new_assignee
            task.status = 'Pending'
            task.save()
            JobHistory.objects.create(
                job=task,
                action='Transferred',
                performed_by=request.user,
                details=f'Task transferred to {new_assignee.username}.'
            )
            messages.success(request, f"Task transferred to {new_assignee.username}.")
            return redirect('task_detail', task_id=task.id)
        except User.DoesNotExist:
            messages.error(request, "Invalid user selected.")

    users = User.objects.all()
    return render(request, 'tasks/transfer_task.html', {'task': task, 'users': users})


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
            messages.success(request, 'Task created successfully.')
            return redirect('task_list')
        else:
            messages.error(request, 'Failed to create task. Please check the input.')
    else:
        form = JobForm()

    return render(request, 'tasks/create_task.html', {'form': form})


@login_required
def edit_task_view(request, task_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to edit this task.")

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


def home_view(request):
    return render(request, 'home.html')
