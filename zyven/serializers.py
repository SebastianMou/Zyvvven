from rest_framework import serializers
from .models import Lead, Client, Project, Task, Note


class NoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['id', 'body', 'author', 'author_name', 'created_at',
                  'lead', 'client', 'project']
        read_only_fields = ['author', 'created_at']

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username if obj.author else 'Unknown'


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'priority', 'status',
                  'assigned_to', 'assigned_to_name', 'due_date',
                  'completed_at', 'created_at', 'project', 'lead']

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() or obj.assigned_to.username if obj.assigned_to else None


class LeadSerializer(serializers.ModelSerializer):
    tasks           = TaskSerializer(many=True, read_only=True)
    assigned_to_name= serializers.SerializerMethodField()
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    source_display  = serializers.CharField(source='get_source_display', read_only=True)
    service_display = serializers.CharField(source='get_service_interest_display', read_only=True)

    class Meta:
        model = Lead
        fields = '__all__'

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() or obj.assigned_to.username if obj.assigned_to else None


class ClientSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    project_count    = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = '__all__'

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() or obj.assigned_to.username if obj.assigned_to else None

    def get_project_count(self, obj):
        return obj.projects.count()


class ProjectSerializer(serializers.ModelSerializer):
    tasks           = TaskSerializer(many=True, read_only=True)
    client_name     = serializers.CharField(source='client.company_name', read_only=True)
    assigned_to_name= serializers.SerializerMethodField()
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    service_display = serializers.CharField(source='get_service_type_display', read_only=True)
    balance_due     = serializers.ReadOnlyField()
    days_since_start= serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() or obj.assigned_to.username if obj.assigned_to else None