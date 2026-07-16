from django.db import models


class OfflineModelSetting(models.Model):
    """Selected local model configuration for desktop/offline AI services."""

    KIND_CHOICES = (
        ("stt", "Speech to text"),
        ("llm", "Language model"),
    )

    kind = models.CharField(max_length=16, choices=KIND_CHOICES, unique=True)
    model_id = models.CharField(max_length=100)
    model_path = models.TextField(blank=True)
    is_downloaded = models.BooleanField(default=False)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "offline_model_settings"

    def __str__(self):
        return f"{self.kind}: {self.model_id}"


class Meeting(models.Model):
    """A local live system-audio meeting capture session."""

    STATUS_CHOICES = (
        ("created", "Created"),
        ("recording", "Recording"),
        ("transcribing", "Transcribing"),
        ("summarizing", "Summarizing"),
        ("building_mom", "Building MOM"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    )

    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="created", db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    audio_source = models.CharField(max_length=80, blank=True)
    stt_model_id = models.CharField(max_length=100, blank=True)
    llm_model_id = models.CharField(max_length=100, blank=True)
    final_mom = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        "db.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meetings"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Meeting {self.pk}"


class TranscriptSegment(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="segments")
    sequence = models.PositiveIntegerField()
    start_seconds = models.FloatField()
    end_seconds = models.FloatField()
    text = models.TextField()
    is_final = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transcript_segments"
        ordering = ["meeting_id", "sequence"]
        constraints = [
            models.UniqueConstraint(fields=["meeting", "sequence"], name="unique_meeting_segment_sequence"),
        ]

    def __str__(self):
        return f"{self.meeting_id} [{self.start_seconds:.1f}-{self.end_seconds:.1f}]"


class MeetingSummary(models.Model):
    SUMMARY_CHOICES = (
        ("chunk", "Chunk"),
        ("merged", "Merged"),
        ("final", "Final"),
    )

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="summaries")
    summary_type = models.CharField(max_length=16, choices=SUMMARY_CHOICES, default="chunk")
    chunk_index = models.PositiveIntegerField(null=True, blank=True)
    start_seconds = models.FloatField(null=True, blank=True)
    end_seconds = models.FloatField(null=True, blank=True)
    summary_markdown = models.TextField()
    source_segment_start = models.PositiveIntegerField(null=True, blank=True)
    source_segment_end = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "meeting_summaries"
        ordering = ["meeting_id", "summary_type", "chunk_index", "created_at"]

    def __str__(self):
        return f"{self.meeting_id} {self.summary_type} {self.chunk_index}"


class MeetingExport(models.Model):
    FORMAT_CHOICES = (
        ("markdown", "Markdown"),
        ("txt", "TXT"),
        ("docx", "DOCX"),
        ("pdf", "PDF"),
    )

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="exports")
    export_format = models.CharField(max_length=16, choices=FORMAT_CHOICES)
    file_path = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "meeting_exports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.meeting_id} {self.export_format}"
