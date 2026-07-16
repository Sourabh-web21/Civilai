from rest_framework import serializers
from db.models import *
from .models import Meeting, MeetingExport, MeetingSummary, OfflineModelSetting, TranscriptSegment

# serializers.py


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'role', 'phone']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserMiniSerializer(read_only=True)
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'due_date', 'priority', 'status', 'assigned_to','start_date']


class TaskDetailSerializer(serializers.ModelSerializer):
    assigned_to = UserMiniSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='assigned_to', write_only=True
    )
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'due_date',
            'project', 'project_name', 'assigned_to', 'assigned_to_id',
            'created_at', 'updated_at'
        ]

        
class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)  # 'tasks' is the related_name in your Task model

    class Meta:
        model = Project
        fields = ['id', 'name', 'sanction_date', 'length_km', 'total_project_cost', 
                  'lane_configuration', 'contractor_name', 'tender_amount', 
                  'completion_period_months', 'appointed_date', 
                  'scheduled_completion_date', 'total_delay_days', 
                  'physical_progress', 'financial_progress', 'status', 
                  'state', 'created_at', 'updated_at', 'tasks']


    def validate_total_project_cost(self, value):
        """
        Ensure total project cost is a positive value.
        """
        if value <= 0:
            raise serializers.ValidationError("Total project cost must be greater than zero.")
        return value

    def validate_tender_amount(self, value):
        """
        Ensure tender amount is a positive value.
        """
        if value <= 0:
            raise serializers.ValidationError("Tender amount must be greater than zero.")
        return value

    def validate_physical_progress(self, value):
        """
        Ensure physical progress is between 0 and 100.
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("Physical progress must be between 0 and 100.")
        return value

    def validate_financial_progress(self, value):
        """
        Ensure financial progress is between 0 and 100.
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("Financial progress must be between 0 and 100.")
        return value


class SummaryCountSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    new = serializers.IntegerField()
    ongoing = serializers.IntegerField()
    on_hold = serializers.IntegerField()
    completed = serializers.IntegerField()

class DashboardSummarySerializer(serializers.Serializer):
    projects = SummaryCountSerializer()
    tasks = SummaryCountSerializer()


class OfflineModelSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineModelSetting
        fields = [
            'id', 'kind', 'model_id', 'model_path', 'is_downloaded',
            'checksum_sha256', 'settings', 'created_at', 'updated_at'
        ]


class TranscriptSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSegment
        fields = [
            'id', 'sequence', 'start_seconds', 'end_seconds', 'text',
            'is_final', 'created_at'
        ]


class MeetingSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingSummary
        fields = [
            'id', 'summary_type', 'chunk_index', 'start_seconds', 'end_seconds',
            'summary_markdown', 'source_segment_start', 'source_segment_end',
            'created_at'
        ]


class MeetingExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingExport
        fields = ['id', 'export_format', 'file_path', 'created_at']


class MeetingSerializer(serializers.ModelSerializer):
    segment_count = serializers.IntegerField(read_only=True)
    summary_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'status', 'started_at', 'stopped_at',
            'duration_seconds', 'audio_source', 'stt_model_id', 'llm_model_id',
            'final_mom', 'error_message', 'metadata', 'segment_count',
            'summary_count', 'created_at', 'updated_at'
        ]


class LocalMeetingStartSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    audio_source = serializers.CharField(required=False, allow_blank=True, max_length=80)


class SegmentInputSerializer(serializers.Serializer):
    start_seconds = serializers.FloatField(min_value=0)
    end_seconds = serializers.FloatField(min_value=0)
    text = serializers.CharField(allow_blank=False, max_length=10000)
    is_final = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        if attrs['end_seconds'] < attrs['start_seconds']:
            raise serializers.ValidationError("end_seconds must be greater than or equal to start_seconds.")
        return attrs


class AppendSegmentsSerializer(serializers.Serializer):
    segments = SegmentInputSerializer(many=True)

    def validate_segments(self, value):
        if not value:
            raise serializers.ValidationError("At least one segment is required.")
        if len(value) > 100:
            raise serializers.ValidationError("Append at most 100 segments per request.")
        return value


class MeetingExportRequestSerializer(serializers.Serializer):
    export_format = serializers.ChoiceField(choices=['markdown', 'txt', 'docx', 'pdf'])
