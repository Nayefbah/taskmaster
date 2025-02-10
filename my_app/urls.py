from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.task_list_view, name='task_list'),
    path('create/', views.create_task_view, name='create_task'),
    path('<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('<int:task_id>/edit/', views.edit_task_view, name='edit_task'),
    path('<int:task_id>/history/', views.task_history_view, name='task_history'),
    path('<int:task_id>/add-note/', views.add_note_view, name='add_note'),
    path('<int:task_id>/change-status/', views.change_task_status_view, name='change_status'),
    path('<int:task_id>/transfer/', views.transfer_task_view, name='transfer_task'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='task_list'), name='logout'),
    path('<int:task_id>/complete/', views.complete_task_view, name='complete_task'),
    path('<int:task_id>/change-status/', views.change_task_status_view, name='change_status'),
]
