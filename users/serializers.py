from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib import auth
from db.models import *

class LoginSerializer(serializers.Serializer): 
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    image = serializers.CharField(read_only=True)
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = User.objects.get(email=obj['email'])
        refresh = RefreshToken.for_user(user)  # Generate JWT tokens
        return {
            # 'refresh_token': str(refresh),
            'access_token': str(refresh.access_token)
        }

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')

        user = auth.authenticate(email=email, password=password)
        if not user:
            raise AuthenticationFailed('Invalid credentials, try again')

        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')

        return {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.first_name,
            'phone': user.phone,
            'image': user.image,
            'tokens': self.get_tokens({'email': user.email}),
        }



class UserSerializer(serializers.ModelSerializer):
    total_tasks = serializers.SerializerMethodField()
    pending_tasks = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password','reset_token','role','groups','user_permissions','is_staff','is_active','is_superuser','last_login','created_at','updated_at']  # Hide password in GET requests

    def get_total_tasks(self, obj):
        return Task.objects.filter(assigned_to=obj).count()

    def get_pending_tasks(self, obj):
        return Task.objects.filter(assigned_to=obj, status='pending').count()

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name','last_name','email',  'phone', 'role', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'image','username']


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_token = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        email = data.get("email")
        reset_token = data.get("reset_token")
        try:
            user = User.objects.get(email=email, reset_token=reset_token)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid token or email.")
        return data