from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Lead(models.Model):
    STATUS_CHOICES = [
        ('new',         'New'),
        ('contacted',   'Contacted'),
        ('blueprint',   'Blueprint Session Scheduled'),
        ('proposal',    'Proposal Sent'),
        ('won',         'Won'),
        ('lost',        'Lost'),
    ]
    SOURCE_CHOICES = [
        ('website',     'Website'),
        ('referral',    'Referral'),
        ('linkedin',    'LinkedIn'),
        ('cold',        'Cold Outreach'),
        ('other',       'Other'),
    ]
    SERVICE_CHOICES = [
        ('audit',       'System Audit & Optimization'),
        ('web',         'Web & App Development'),
        ('ai',          'AI & Automation Builds'),
        ('managed',     'Managed Services'),
        ('mixed',       'Multiple Services'),
    ]

    # Contact info
    company_name    = models.CharField(max_length=200)
    contact_name    = models.CharField(max_length=200)
    email           = models.EmailField()
    phone           = models.CharField(max_length=50, blank=True)
    website         = models.URLField(blank=True)

    # Deal info
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    source          = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')
    service_interest= models.CharField(max_length=20, choices=SERVICE_CHOICES, default='audit')
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pain_points     = models.TextField(blank=True, help_text='Describe what problems the lead mentioned')

    # Meta
    assigned_to     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    blueprint_date  = models.DateTimeField(null=True, blank=True, help_text='Blueprint session scheduled date')
    notes           = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name} — {self.contact_name}"


class Client(models.Model):
    # Converted from a Lead (optional link)
    lead            = models.OneToOneField(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='client')
    company_name    = models.CharField(max_length=200)
    contact_name    = models.CharField(max_length=200)
    email           = models.EmailField()
    phone           = models.CharField(max_length=50, blank=True)
    website         = models.URLField(blank=True)
    industry        = models.CharField(max_length=100, blank=True)
    assigned_to     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')
    created_at      = models.DateTimeField(auto_now_add=True)
    notes           = models.TextField(blank=True)
    is_active       = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name}"


class Project(models.Model):
    STATUS_CHOICES = [
        ('scoping',     'Scoping'),
        ('active',      'Active — Building'),
        ('beta',        'Beta (Days 1–7)'),
        ('launch',      'Full Launch (Days 8–14)'),
        ('managed',     'Managed / Ongoing'),
        ('completed',   'Completed'),
        ('paused',      'Paused'),
    ]
    SERVICE_CHOICES = [
        ('audit',       'System Audit & Optimization'),
        ('web',         'Web & App Development'),
        ('ai',          'AI & Automation Builds'),
        ('managed',     'Managed Services'),
        ('mixed',       'Multiple Services'),
    ]

    client          = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    name            = models.CharField(max_length=200)
    service_type    = models.CharField(max_length=20, choices=SERVICE_CHOICES, default='web')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scoping')
    description     = models.TextField(blank=True)

    # Financials
    fixed_price     = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    amount_paid     = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Timeline
    start_date      = models.DateField(null=True, blank=True)
    beta_date       = models.DateField(null=True, blank=True, help_text='Target Day 7 beta date')
    launch_date     = models.DateField(null=True, blank=True, help_text='Target Day 14 launch date')

    assigned_to     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.client.company_name})"

    @property
    def balance_due(self):
        if self.fixed_price:
            return self.fixed_price - self.amount_paid
        return None

    @property
    def days_since_start(self):
        if self.start_date:
            return (timezone.now().date() - self.start_date).days
        return None


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low',     'Low'),
        ('medium',  'Medium'),
        ('high',    'High'),
        ('urgent',  'Urgent'),
    ]
    STATUS_CHOICES = [
        ('todo',        'To Do'),
        ('in_progress', 'In Progress'),
        ('done',        'Done'),
    ]

    project         = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    lead            = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title           = models.CharField(max_length=300)
    description     = models.TextField(blank=True)
    priority        = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo')
    assigned_to     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    due_date        = models.DateField(null=True, blank=True)
    completed_at    = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', '-priority']

    def __str__(self):
        return self.title


class Note(models.Model):
    lead            = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='note_entries', null=True, blank=True)
    client          = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='note_entries', null=True, blank=True)
    project         = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='note_entries', null=True, blank=True)
    author          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    body            = models.TextField()
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by {self.author} on {self.created_at.strftime('%Y-%m-%d')}"