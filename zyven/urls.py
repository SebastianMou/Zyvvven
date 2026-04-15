from django.urls import path
from . import views

app_name = 'zyven'

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('crm/login/',  views.crm_login, name='crm_login'),
    path('crm/logout/', views.crm_logout, name='crm_logout'),

    # Dashboard
    path('crm/',views.dashboard,name='dashboard'),

    # Leads
    path('crm/leads/',views.lead_list,name='lead_list'),
    path('crm/leads/new/',views.lead_create,name='lead_create'),
    path('crm/leads/<int:pk>/',views.lead_detail,name='lead_detail'),
    path('crm/leads/<int:pk>/edit/',views.lead_edit,name='lead_edit'),
    path('crm/leads/<int:pk>/convert/',views.lead_convert,name='lead_convert'),

    # Clients
    path('crm/clients/',views.client_list,name='client_list'),
    path('crm/clients/new/',views.client_create,name='client_create'),
    path('crm/clients/<int:pk>/',views.client_detail,name='client_detail'),
    path('crm/clients/<int:pk>/edit/',views.client_edit,name='client_edit'),

    # Projects
    path('crm/projects/',views.project_list,name='project_list'),
    path('crm/projects/new/',views.project_create,name='project_create'),
    path('crm/projects/<int:pk>/',views.project_detail,name='project_detail'),
    path('crm/projects/<int:pk>/edit/', views.project_edit,name='project_edit'),

    # Tasks
    path('crm/tasks/',views.task_list,name='task_list'),
    path('crm/tasks/new/',views.task_create,name='task_create'),
    path('crm/tasks/<int:pk>/toggle/',views.task_toggle,name='task_toggle'),

    # Notes
    path('crm/notes/new/',views.note_create,name='note_create'),

    # API
    path('api/leads/',views.api_leads,name='api_leads'),
    path('api/projects/',views.api_projects,name='api_projects'),
    path('api/tasks/',views.api_tasks,name='api_tasks'),
    path('api/chat/',views.chat_api,name='chat_api'),
    path('api/chat/history/', views.chat_history, name='chat_history'),

    # articales
    path('ideaconv/', views.ideaconv, name='ideaconv'),
    path('six-cias/', views.six_cias, name='six_cias'),
    path('riosa-sticker/', views.riosa_sticker, name='riosa_sticker'),
    path('bahia/', views.bahia, name='bahia'),
    path('whatsbizpro/', views.whatsbizpro, name='whatsbizpro'),
]