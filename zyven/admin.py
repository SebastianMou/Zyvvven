from django.contrib import admin
from .models import Lead, Client, Project, Task, Note


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display    = ['company_name', 'contact_name', 'email', 'status', 'service_interest', 'estimated_value', 'assigned_to', 'created_at']
    list_filter     = ['status', 'source', 'service_interest', 'assigned_to']
    search_fields   = ['company_name', 'contact_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Contact Info', {
            'fields': ('company_name', 'contact_name', 'email', 'phone', 'website')
        }),
        ('Deal Info', {
            'fields': ('status', 'source', 'service_interest', 'estimated_value', 'pain_points', 'blueprint_date')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display    = ['company_name', 'contact_name', 'email', 'industry', 'is_active', 'assigned_to', 'created_at']
    list_filter     = ['is_active', 'assigned_to', 'industry']
    search_fields   = ['company_name', 'contact_name', 'email']
    readonly_fields = ['created_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display    = ['name', 'client', 'service_type', 'status', 'fixed_price', 'amount_paid', 'start_date', 'launch_date', 'assigned_to']
    list_filter     = ['status', 'service_type', 'assigned_to']
    search_fields   = ['name', 'client__company_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Project Info', {
            'fields': ('client', 'name', 'service_type', 'status', 'description')
        }),
        ('Financials', {
            'fields': ('fixed_price', 'amount_paid')
        }),
        ('Timeline', {
            'fields': ('start_date', 'beta_date', 'launch_date')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display    = ['title', 'project', 'lead', 'priority', 'status', 'assigned_to', 'due_date']
    list_filter     = ['status', 'priority', 'assigned_to']
    search_fields   = ['title', 'project__name', 'lead__company_name']
    readonly_fields = ['created_at', 'completed_at']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display    = ['__str__', 'lead', 'client', 'project', 'author', 'created_at']
    list_filter     = ['author']
    search_fields   = ['body']
    readonly_fields = ['created_at']