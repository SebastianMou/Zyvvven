# Django CRM Documentation

## Overview
This is a comprehensive documentation for the Django CRM application that helps manage leads, clients, projects, and tasks effectively.

## Features
- **Lead Tracking**: Manage sales pipelines with various statuses.
- **Client Management**: Track converted leads along with their company information.
- **Project Management**: Handle client work with financial tracking.
- **Task Management**: Prioritize and track tasks associated with projects.
- **Notes**: Keep communications linked to leads, clients, and projects.

## Models
### Lead
- **Statuses**: New, Contacted, Blueprint Session, Proposal, Won, Lost
- **Sources**: Website, Referral, LinkedIn, Cold Outreach, Other

### Client
- Stores information of converted leads and their active status.

### Project
- **Statuses**: Scoping, Active, Beta, Full Launch, Managed, Completed, Paused
- Tracks financial information.

### Task
- **Priorities**: Low, Medium, High, Urgent
- **Statuses**: To Do, In Progress, Done

### Note
- Stores communication details linked to leads, clients, and projects.

## API Endpoints
- **Leads**: `/api/leads/`
- **Projects**: `/api/projects/`
- **Tasks**: `/api/tasks/`
- **Authentication**: `/crm/login/`
- **Dashboard**: `/crm/`

## Installation Instructions
1. Clone the repository.
2. Install required packages.
3. Apply database migrations.
4. Create superuser for admin access.
5. Start the development server.

## Project Structure
```plaintext
├── crm/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py
│   └── ...
├── templates/
│   └── ...
└── manage.py
```

## Usage Examples
### Creating a Lead
```python
# Example code for creating a lead
lead = Lead(name='John Doe', source='Website', status='New')
lead.save()
```

### Fetching Projects
```python
# Example code for fetching projects
projects = Project.objects.all()
```
