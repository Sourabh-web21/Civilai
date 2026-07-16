from django.urls import path

from .views import CivilAIQueryAPIView, RagReloadAPIView

urlpatterns = [
    path('generate', CivilAIQueryAPIView.as_view(), name='chat-generate'),
    path('reload', RagReloadAPIView.as_view(), name='chat-reload'),
]
