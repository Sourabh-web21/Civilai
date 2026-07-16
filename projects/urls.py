from django.urls import path
from .views import *
from .extract import *
from .email_actions import EmailActionView
from .local_meeting_views import (
    LocalMeetingAppendSegmentsView,
    LocalMeetingBackendStatusView,
    LocalMeetingDetailView,
    LocalMeetingExportView,
    LocalMeetingMomView,
    LocalMeetingStartView,
    LocalMeetingStatusView,
    LocalMeetingStopView,
)
from .meetings import MeetingBotStartView, MeetingMomView
from .model_views import OfflineModelDownloadView, OfflineModelListView
urlpatterns = [
    path('list', ProjectAPIView.as_view(), name='project-list'),
    path('list/<int:project_id>', ProjectDetailAPIView.as_view(), name='project-detail'),
    path('tasks/list', TaskListCreateAPIView.as_view(), name='task-list-create'),
    path('tasks/list/<int:pk>', TaskDetailAPIView.as_view(), name='task-detail'),
    path('dashboard', DashboardSummaryAPIView.as_view(), name='dashboard'),
    path('extract',EmailExtractorView.as_view(), name='extract'),
    path('email/action', EmailActionView.as_view(), name='email-action'),
    path('meeting/start', MeetingBotStartView.as_view(), name='meeting-start'),
    path('meeting/mom', MeetingMomView.as_view(), name='meeting-mom'),
    path('local-meeting/start', LocalMeetingStartView.as_view(), name='local-meeting-start'),
    path('local-meeting/backend-status', LocalMeetingBackendStatusView.as_view(), name='local-meeting-backend-status'),
    path('local-meeting/<int:meeting_id>', LocalMeetingDetailView.as_view(), name='local-meeting-detail'),
    path('local-meeting/<int:meeting_id>/status', LocalMeetingStatusView.as_view(), name='local-meeting-status'),
    path('local-meeting/<int:meeting_id>/segments', LocalMeetingAppendSegmentsView.as_view(), name='local-meeting-segments'),
    path('local-meeting/<int:meeting_id>/stop', LocalMeetingStopView.as_view(), name='local-meeting-stop'),
    path('local-meeting/<int:meeting_id>/mom', LocalMeetingMomView.as_view(), name='local-meeting-mom'),
    path('local-meeting/<int:meeting_id>/export', LocalMeetingExportView.as_view(), name='local-meeting-export'),
    path('offline-models', OfflineModelListView.as_view(), name='offline-model-list'),
    path('offline-models/<str:model_id>/download', OfflineModelDownloadView.as_view(), name='offline-model-download'),
]
