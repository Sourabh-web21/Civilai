from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from .models import (
    Meeting,
    MeetingExport,
    MeetingSummary,
    OfflineModelSetting,
    TranscriptSegment,
)


class OfflineModelSettingAdmin(admin.ModelAdmin):
    list_display = ("kind", "model_id", "is_downloaded", "updated_at")
    search_fields = ("kind", "model_id", "model_path")
    readonly_fields = ("created_at", "updated_at")


class TranscriptSegmentInline(admin.TabularInline):
    model = TranscriptSegment
    extra = 0
    fields = ("sequence", "start_seconds", "end_seconds", "is_final", "text")
    readonly_fields = ("sequence", "start_seconds", "end_seconds", "is_final", "text")
    can_delete = False


class MeetingSummaryInline(admin.TabularInline):
    model = MeetingSummary
    extra = 0
    fields = ("summary_type", "chunk_index", "start_seconds", "end_seconds", "created_at")
    readonly_fields = ("summary_type", "chunk_index", "start_seconds", "end_seconds", "created_at")
    can_delete = False


class MeetingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "started_at", "stopped_at", "created_by")
    list_filter = ("status", "created_at")
    search_fields = ("title", "final_mom", "error_message")
    readonly_fields = ("created_at", "updated_at")
    inlines = (TranscriptSegmentInline, MeetingSummaryInline)


class TranscriptSegmentAdmin(admin.ModelAdmin):
    list_display = ("meeting", "sequence", "start_seconds", "end_seconds", "is_final")
    list_filter = ("is_final", "created_at")
    search_fields = ("text",)


class MeetingSummaryAdmin(admin.ModelAdmin):
    list_display = ("meeting", "summary_type", "chunk_index", "start_seconds", "end_seconds", "created_at")
    list_filter = ("summary_type", "created_at")
    search_fields = ("summary_markdown",)


class MeetingExportAdmin(admin.ModelAdmin):
    list_display = ("meeting", "export_format", "file_path", "created_at")
    list_filter = ("export_format", "created_at")
    search_fields = ("file_path",)


def safe_register(model, admin_class):
    try:
        admin.site.register(model, admin_class)
    except AlreadyRegistered:
        pass


safe_register(OfflineModelSetting, OfflineModelSettingAdmin)
safe_register(Meeting, MeetingAdmin)
safe_register(TranscriptSegment, TranscriptSegmentAdmin)
safe_register(MeetingSummary, MeetingSummaryAdmin)
safe_register(MeetingExport, MeetingExportAdmin)
