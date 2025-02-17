from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.task_list_view, name='task_list'),
    path('create/', views.create_task_view, name='create_task'),
    path('<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('<int:task_id>/history/', views.task_history_view, name='task_history'),
    path('<int:task_id>/add-note/', views.add_note_view, name='add_note'),
    path('<int:task_id>/change-status/', views.change_task_status_view, name='change_status'),
    path('<int:task_id>/transfer/', views.transfer_task_view, name='transfer_task'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='task_list'), name='logout'),
    path('<int:task_id>/complete/', views.complete_task_view, name='complete_task'),
    path('<int:task_id>/change-status/', views.change_task_status_view, name='change_status'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('tasks/<int:task_id>/delete-last-note/',views.delete_last_note, name='delete_last_note'),
    path('task-statistics/', views.task_statistics_view, name='task_statistics'),
    path('admin-task-history/', views.admin_history_view, name='admin_task_history'),
    path('signup/', views.signup_view, name='signup'),
    path('manage-users/', views.manage_users_view, name='manage_users'),
]
