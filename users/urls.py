from django.urls import path
from .views import LoginAPIView
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login', LoginAPIView.as_view(), name='login'),
    path('list', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('list/<int:pk>', UserDetailAPIView.as_view(), name='user-detail'),
    path('change-password', ChangePasswordAPIView.as_view(), name='change-password'),
    path('forgot-password', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('reset-password', ResetPasswordAPIView.as_view(), name='reset-password'),
    path('profile', AdminProfileAPIView.as_view(), name='admin-profile'),

    
]
