from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import uuid

from django.views.decorators.csrf import csrf_exempt
from google import genai
from django.contrib.auth import authenticate, login, logout
from .models import Lead, Client, Project, Task, Note, ChatMessage
from .serializers import LeadSerializer, ClientSerializer, ProjectSerializer, TaskSerializer


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────

def home(request):
    return render(request, 'home.html', {})

def six_cias(request):
    return render(request, 'projects/six_cias.html', {})

def ideaconv(request):
    return render(request, 'projects/ideaconv.html', {})

def riosa_sticker(request):
    return render(request, 'projects/riosa_sticker.html', {})

def bahia(request):
    return render(request, 'projects/bahia.html', {})

def whatsbizpro(request):
    return render(request, 'projects/whatsbizpro.html', {})

def crm_login(request):
    if request.user.is_authenticated:
        return redirect('zyven:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('zyven:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'crm/login.html')

def crm_logout(request):
    logout(request)
    return redirect('zyven:crm_login')

@login_required
def dashboard(request):
    # Counts
    total_leads     = Lead.objects.count()
    active_projects = Project.objects.filter(status__in=['active', 'beta', 'launch']).count()
    total_clients   = Client.objects.filter(is_active=True).count()
    won_leads       = Lead.objects.filter(status='won').count()

    # Pipeline value (all open leads with estimated value)
    pipeline_value = Lead.objects.filter(
        status__in=['new', 'contacted', 'blueprint', 'proposal']
    ).aggregate(total=Sum('estimated_value'))['total'] or 0

    # Revenue (projects with payments)
    total_revenue = Project.objects.aggregate(total=Sum('amount_paid'))['total'] or 0

    # Recent leads
    recent_leads = Lead.objects.select_related('assigned_to').order_by('-created_at')[:6]

    # Active projects
    projects = Project.objects.filter(
        status__in=['active', 'beta', 'launch', 'scoping']
    ).select_related('client', 'assigned_to').order_by('-updated_at')[:6]

    # My open tasks
    my_tasks = Task.objects.filter(
        assigned_to=request.user,
        status__in=['todo', 'in_progress']
    ).select_related('project', 'lead').order_by('due_date')[:8]

    # Leads by status for pipeline chart
    lead_pipeline = Lead.objects.values('status').annotate(count=Count('id'))
    pipeline_data = {item['status']: item['count'] for item in lead_pipeline}

    # Upcoming blueprint sessions
    upcoming_blueprints = Lead.objects.filter(
        blueprint_date__gte=timezone.now(),
        status='blueprint'
    ).order_by('blueprint_date')[:4]

    context = {
        'total_leads':          total_leads,
        'active_projects':      active_projects,
        'total_clients':        total_clients,
        'won_leads':            won_leads,
        'pipeline_value':       pipeline_value,
        'total_revenue':        total_revenue,
        'recent_leads':         recent_leads,
        'projects':             projects,
        'my_tasks':             my_tasks,
        'pipeline_data':        json.dumps(pipeline_data),
        'upcoming_blueprints':  upcoming_blueprints,
    }
    return render(request, 'crm/dashboard.html', context)


# ─────────────────────────────────────────────
#  LEADS
# ─────────────────────────────────────────────

@login_required
def lead_list(request):
    qs = Lead.objects.select_related('assigned_to').all()

    # Filters
    status  = request.GET.get('status', '')
    source  = request.GET.get('source', '')
    service = request.GET.get('service', '')
    search  = request.GET.get('q', '')

    if status:
        qs = qs.filter(status=status)
    if source:
        qs = qs.filter(source=source)
    if service:
        qs = qs.filter(service_interest=service)
    if search:
        qs = qs.filter(
            Q(company_name__icontains=search) |
            Q(contact_name__icontains=search) |
            Q(email__icontains=search)
        )

    context = {
        'leads':            qs,
        'status_choices':   Lead.STATUS_CHOICES,
        'source_choices':   Lead.SOURCE_CHOICES,
        'service_choices':  Lead.SERVICE_CHOICES,
        'current_status':   status,
        'current_source':   source,
        'current_service':  service,
        'search':           search,
    }
    return render(request, 'crm/lead_list.html', context)


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    notes = lead.note_entries.select_related('author').all()
    tasks = lead.tasks.select_related('assigned_to').all()
    context = {'lead': lead, 'notes': notes, 'tasks': tasks}
    return render(request, 'crm/lead_detail.html', context)


@login_required
def lead_create(request):
    if request.method == 'POST':
        data = request.POST
        lead = Lead.objects.create(
            company_name        = data.get('company_name'),
            contact_name        = data.get('contact_name'),
            email               = data.get('email'),
            phone               = data.get('phone', ''),
            website             = data.get('website', ''),
            status              = data.get('status', 'new'),
            source              = data.get('source', 'website'),
            service_interest    = data.get('service_interest', 'audit'),
            estimated_value     = data.get('estimated_value') or None,
            pain_points         = data.get('pain_points', ''),
            notes               = data.get('notes', ''),
            assigned_to         = request.user,
        )
        messages.success(request, f'Lead "{lead.company_name}" created.')
        return redirect('zyven:lead_detail', pk=lead.pk)
    context = {
        'status_choices':   Lead.STATUS_CHOICES,
        'source_choices':   Lead.SOURCE_CHOICES,
        'service_choices':  Lead.SERVICE_CHOICES,
    }
    return render(request, 'crm/lead_form.html', context)


@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        data = request.POST
        lead.company_name       = data.get('company_name')
        lead.contact_name       = data.get('contact_name')
        lead.email              = data.get('email')
        lead.phone              = data.get('phone', '')
        lead.website            = data.get('website', '')
        lead.status             = data.get('status', lead.status)
        lead.source             = data.get('source', lead.source)
        lead.service_interest   = data.get('service_interest', lead.service_interest)
        lead.estimated_value    = data.get('estimated_value') or None
        lead.pain_points        = data.get('pain_points', '')
        lead.notes              = data.get('notes', '')
        lead.save()
        messages.success(request, 'Lead updated.')
        return redirect('zyven:lead_detail', pk=lead.pk)
    context = {
        'lead':             lead,
        'status_choices':   Lead.STATUS_CHOICES,
        'source_choices':   Lead.SOURCE_CHOICES,
        'service_choices':  Lead.SERVICE_CHOICES,
    }
    return render(request, 'crm/lead_form.html', context)


@login_required
def lead_convert(request, pk):
    """Convert a won lead into a Client."""
    lead = get_object_or_404(Lead, pk=pk)
    if hasattr(lead, 'client'):
        messages.info(request, 'This lead has already been converted.')
        return redirect('zyven:client_detail', pk=lead.client.pk)
    client = Client.objects.create(
        lead            = lead,
        company_name    = lead.company_name,
        contact_name    = lead.contact_name,
        email           = lead.email,
        phone           = lead.phone,
        website         = lead.website,
        assigned_to     = lead.assigned_to,
        notes           = lead.notes,
    )
    lead.status = 'won'
    lead.save()
    messages.success(request, f'Lead converted to client: {client.company_name}')
    return redirect('zyven:client_detail', pk=client.pk)


# ─────────────────────────────────────────────
#  CLIENTS
# ─────────────────────────────────────────────

@login_required
def client_list(request):
    qs = Client.objects.select_related('assigned_to').prefetch_related('projects')
    search = request.GET.get('q', '')
    active = request.GET.get('active', '')

    if search:
        qs = qs.filter(
            Q(company_name__icontains=search) |
            Q(contact_name__icontains=search) |
            Q(email__icontains=search)
        )
    if active == '1':
        qs = qs.filter(is_active=True)
    elif active == '0':
        qs = qs.filter(is_active=False)

    context = {'clients': qs, 'search': search, 'active': active}
    return render(request, 'crm/client_list.html', context)


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    projects = client.projects.select_related('assigned_to').all()
    notes    = client.note_entries.select_related('author').all()
    context  = {'client': client, 'projects': projects, 'notes': notes}
    return render(request, 'crm/client_detail.html', context)


@login_required
def client_create(request):
    if request.method == 'POST':
        data = request.POST
        client = Client.objects.create(
            company_name    = data.get('company_name'),
            contact_name    = data.get('contact_name'),
            email           = data.get('email'),
            phone           = data.get('phone', ''),
            website         = data.get('website', ''),
            industry        = data.get('industry', ''),
            notes           = data.get('notes', ''),
            assigned_to     = request.user,
        )
        messages.success(request, f'Client "{client.company_name}" created.')
        return redirect('zyven:client_detail', pk=client.pk)
    return render(request, 'crm/client_form.html', {})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        data = request.POST
        client.company_name = data.get('company_name')
        client.contact_name = data.get('contact_name')
        client.email        = data.get('email')
        client.phone        = data.get('phone', '')
        client.website      = data.get('website', '')
        client.industry     = data.get('industry', '')
        client.notes        = data.get('notes', '')
        client.is_active    = data.get('is_active') == 'on'
        client.save()
        messages.success(request, 'Client updated.')
        return redirect('zyven:client_detail', pk=client.pk)
    return render(request, 'crm/client_form.html', {'client': client})


# ─────────────────────────────────────────────
#  PROJECTS
# ─────────────────────────────────────────────

@login_required
def project_list(request):
    qs = Project.objects.select_related('client', 'assigned_to').all()
    status  = request.GET.get('status', '')
    search  = request.GET.get('q', '')

    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(client__company_name__icontains=search)
        )

    context = {
        'projects':         qs,
        'status_choices':   Project.STATUS_CHOICES,
        'current_status':   status,
        'search':           search,
    }
    return render(request, 'crm/project_list.html', context)


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    tasks   = project.tasks.select_related('assigned_to').all()
    notes   = project.note_entries.select_related('author').all()
    context = {'project': project, 'tasks': tasks, 'notes': notes}
    return render(request, 'crm/project_detail.html', context)


@login_required
def project_create(request):
    clients = Client.objects.filter(is_active=True)
    if request.method == 'POST':
        data = request.POST
        project = Project.objects.create(
            client          = get_object_or_404(Client, pk=data.get('client')),
            name            = data.get('name'),
            service_type    = data.get('service_type', 'web'),
            status          = data.get('status', 'scoping'),
            description     = data.get('description', ''),
            fixed_price     = data.get('fixed_price') or None,
            amount_paid     = data.get('amount_paid') or 0,
            start_date      = data.get('start_date') or None,
            beta_date       = data.get('beta_date') or None,
            launch_date     = data.get('launch_date') or None,
            assigned_to     = request.user,
        )
        messages.success(request, f'Project "{project.name}" created.')
        return redirect('zyven:project_detail', pk=project.pk)
    context = {
        'clients':          clients,
        'status_choices':   Project.STATUS_CHOICES,
        'service_choices':  Project.SERVICE_CHOICES,
    }
    return render(request, 'crm/project_form.html', context)


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    clients = Client.objects.filter(is_active=True)
    if request.method == 'POST':
        data = request.POST
        project.client      = get_object_or_404(Client, pk=data.get('client'))
        project.name        = data.get('name')
        project.service_type= data.get('service_type', project.service_type)
        project.status      = data.get('status', project.status)
        project.description = data.get('description', '')
        project.fixed_price = data.get('fixed_price') or None
        project.amount_paid = data.get('amount_paid') or 0
        project.start_date  = data.get('start_date') or None
        project.beta_date   = data.get('beta_date') or None
        project.launch_date = data.get('launch_date') or None
        project.save()
        messages.success(request, 'Project updated.')
        return redirect('zyven:project_detail', pk=project.pk)
    context = {
        'project':          project,
        'clients':          clients,
        'status_choices':   Project.STATUS_CHOICES,
        'service_choices':  Project.SERVICE_CHOICES,
    }
    return render(request, 'crm/project_form.html', context)


# ─────────────────────────────────────────────
#  TASKS
# ─────────────────────────────────────────────

@login_required
def task_list(request):
    qs = Task.objects.select_related('project', 'lead', 'assigned_to').all()
    status   = request.GET.get('status', '')
    priority = request.GET.get('priority', '')

    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)

    context = {
        'tasks':            qs,
        'status_choices':   Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'current_status':   status,
        'current_priority': priority,
    }
    return render(request, 'crm/task_list.html', context)


@login_required
@require_POST
def task_create(request):
    data = request.POST
    project_id  = data.get('project')
    lead_id     = data.get('lead')
    task = Task.objects.create(
        title       = data.get('title'),
        description = data.get('description', ''),
        priority    = data.get('priority', 'medium'),
        status      = 'todo',
        due_date    = data.get('due_date') or None,
        assigned_to = request.user,
        project     = get_object_or_404(Project, pk=project_id) if project_id else None,
        lead        = get_object_or_404(Lead, pk=lead_id) if lead_id else None,
    )
    messages.success(request, f'Task "{task.title}" created.')
    # Redirect back to where we came from
    next_url = request.POST.get('next', 'zyven:task_list')
    if project_id:
        return redirect('zyven:project_detail', pk=project_id)
    if lead_id:
        return redirect('zyven:lead_detail', pk=lead_id)
    return redirect('zyven:task_list')


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.status == 'done':
        task.status         = 'todo'
        task.completed_at   = None
    else:
        task.status         = 'done'
        task.completed_at   = timezone.now()
    task.save()
    return JsonResponse({'status': task.status})


# ─────────────────────────────────────────────
#  NOTES
# ─────────────────────────────────────────────

@login_required
@require_POST
def note_create(request):
    data        = request.POST
    lead_id     = data.get('lead')
    client_id   = data.get('client')
    project_id  = data.get('project')

    Note.objects.create(
        body        = data.get('body'),
        author      = request.user,
        lead        = get_object_or_404(Lead, pk=lead_id)       if lead_id      else None,
        client      = get_object_or_404(Client, pk=client_id)   if client_id    else None,
        project     = get_object_or_404(Project, pk=project_id) if project_id   else None,
    )
    messages.success(request, 'Note added.')
    if project_id:
        return redirect('zyven:project_detail', pk=project_id)
    if client_id:
        return redirect('zyven:client_detail', pk=client_id)
    if lead_id:
        return redirect('zyven:lead_detail', pk=lead_id)
    return redirect('zyven:dashboard')


# ─────────────────────────────────────────────
#  PUBLIC CHAT API  (Gemini SDK + save)
# ─────────────────────────────────────────────
GEMINI_API_KEY = 'AIzaSyBY6L91zYWZZpPcQRfbYdn3CSrlqkmcVPQ'

ZYVEN_SYSTEM_CONTEXT = """You are Zyven AI, the smart, confident sales assistant for Zyven — a B2B tech consulting company.

ABOUT ZYVEN:
- We build custom systems, automation, and AI for B2B companies in 14 days
- Fixed price, zero surprises — day-one quote = final price
- Free Blueprint Session: 30-min live call where we screen-share a visual map of the client's broken systems + a working prototype of the fix. If we can't find 3 real problems, it's 100% free
- Beta live in 7 days, full production launch in 14 days — this is a guarantee, not a goal
- 60-day "No Orphan Systems" guarantee: we come back and fix anything that breaks, at zero cost
- Tech stack: Django, PostgreSQL, React, Python, Railway, OpenAI, Anthropic Claude
- Services: System Audit & Optimization, Web & App Development, AI & Automation Builds, Managed Services

YOUR PERSONALITY:
- Direct, confident, no fluff
- Speak the language of B2B operators: ROI, efficiency, revenue impact
- Create urgency without being pushy
- Always end by nudging toward booking the Free Blueprint Session
- Keep responses under 120 words — this is a chat widget, not an essay
- Use emojis sparingly but effectively
- CRITICAL: Detect the language of the FIRST user message. If it is Spanish, respond in Spanish for the ENTIRE conversation without exception. If English, stay in English for the entire conversation. Never switch languages mid-conversation.

NEVER:
- Make up pricing numbers (pricing is proposal-based)
- Promise timelines outside the 7/14 day framework
- Discuss competitors by name"""


@csrf_exempt
@require_POST
def chat_api(request):
    try:
        body       = json.loads(request.body)
        user_msg   = body.get('message', '').strip()
        source     = body.get('source', 'fab')
        session_id = body.get('session_id', '')

        if not user_msg:
            return JsonResponse({'error': 'Empty message'}, status=400)

        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['chat_session_id'] = session_id
        
        # Load history from Django session
        history_key = 'chat_inline' if source == 'inline' else 'chat_fab'
        history = request.session.get(history_key, [])

        # Save user message to DB
        ChatMessage.objects.create(
            session_id = session_id,
            role       = 'user',
            message    = user_msg,
            source     = source,
            ip_address = request.META.get('REMOTE_ADDR'),
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:400],
        )

        # Build contents for Gemini
        contents = list(history)
        contents.append({'role': 'user', 'parts': [{'text': user_msg}]})

        # Call Gemini
        client   = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model    = 'gemini-2.5-flash-lite',
            contents = contents,
            config   = {
                'system_instruction': ZYVEN_SYSTEM_CONTEXT,
                'temperature':        0.7,
                'max_output_tokens':  300,
            }
        )

        reply = response.text or "I'm having trouble responding right now. Please try again."

        # Save model reply to DB
        ChatMessage.objects.create(
            session_id = session_id,
            role       = 'model',
            message    = reply,
            source     = source,
            ip_address = request.META.get('REMOTE_ADDR'),
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:400],
        )

        # Update Django session history
        history.append({'role': 'user',  'parts': [{'text': user_msg}]})
        history.append({'role': 'model', 'parts': [{'text': reply}]})
        if len(history) > 20:
            history = history[-20:]
        request.session[history_key] = history
        request.session.modified = True

        return JsonResponse({'reply': reply, 'session_id': session_id})

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
            return JsonResponse({
                'reply': "⚡ Our AI is taking a quick breather. <a href='#contact' style='color:var(--z-blue)'>Book a call directly</a> and we'll get back to you fast."
            }, status=200)
        return JsonResponse({'error': error_msg}, status=500)    

@csrf_exempt
def chat_history(request):
    inline = request.session.get('chat_inline', [])
    fab    = request.session.get('chat_fab', [])
    return JsonResponse({'inline': inline, 'fab': fab})


# ─────────────────────────────────────────────
#  API ENDPOINTS (for AJAX / REST)
# ─────────────────────────────────────────────

@login_required
def api_leads(request):
    leads = Lead.objects.all()
    serializer = LeadSerializer(leads, many=True)
    return JsonResponse(serializer.data, safe=False)


@login_required
def api_projects(request):
    projects = Project.objects.select_related('client').all()
    serializer = ProjectSerializer(projects, many=True)
    return JsonResponse(serializer.data, safe=False)


@login_required
def api_tasks(request):
    tasks = Task.objects.filter(assigned_to=request.user, status__in=['todo', 'in_progress'])
    serializer = TaskSerializer(tasks, many=True)
    return JsonResponse(serializer.data, safe=False)