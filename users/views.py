from rest_framework.views import APIView
from utils.response_utils import CivilResponse, CivilErrorResponse
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import *
from db.models import *
from .serializers import *
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
import random

class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        if 'email' not in request.data or 'password' not in request.data:
            return CivilErrorResponse(
                error_message='Email or Password not provided',
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return CivilErrorResponse(
                error_message=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.get(email=serializer.validated_data['email'])
        response_dict = serializer.data
        response_dict.update({"full_name": user.full_name, "id": user.id})
        return CivilResponse(response_dict, status=status.HTTP_200_OK, is_success="Logged In ")


# List all users and create a new user
class UserListCreateAPIView(APIView):
    def get(self, request):
        users = User.objects.all().order_by('-created_at')
        serializer = UserSerializer(users, many=True)
        try:
            return CivilResponse(serializer.data, status=status.HTTP_200_OK,is_success="Users retrieved successfully")
        except Exception as e:
            return CivilErrorResponse(str(e), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return CivilResponse(UserSerializer(user).data, status=status.HTTP_201_CREATED,is_success="User created successfully")
        return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Retrieve, update, delete a specific user
class UserDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(User, pk=pk)

    def get(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return CivilResponse(serializer.data)

    # def put(self, request, pk):
    #     user = self.get_object(pk)
    #     serializer = UserSerializer(user, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return CivilResponse(serializer.data,is_success="User updated successfully")
    #     return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            user = self.get_object(pk)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return CivilResponse(serializer.data, status=status.HTTP_200_OK,is_success="User updated successfully")
            return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"[PATCH Exception] {e}")
            return CivilErrorResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        user = self.get_object(pk)

        # Block superuser deletion
        if user.is_superuser:
            return CivilErrorResponse(
                {"error": "Cannot delete a superuser."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Block self-deletion
        if request.user == user:
            return CivilErrorResponse(
                {"error": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.delete()
        return CivilResponse(status=status.HTTP_204_NO_CONTENT, is_success="User deleted successfully")


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        user = request.user

        if serializer.is_valid():
            # Check if the old password matches
            if not user.check_password(serializer.validated_data['old_password']):
                return CivilErrorResponse(
                    error_message="Old password is incorrect.",
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Set and save new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return CivilResponse(
                resp_data={},
                is_success="Password changed successfully.",
                status=status.HTTP_200_OK
            )

        return CivilErrorResponse(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = str(random.randint(100000, 999999))
                user.reset_token = token
                user.save()
                try:
                    send_mail(
                        'Password Reset Request',
                        f'Your OTP for password reset is: {token}',
                        None,  # Uses DEFAULT_FROM_EMAIL
                        [email],
                        fail_silently=False,
                    )
                except Exception as e:
                    return CivilErrorResponse({"error": "Unable to send email."}, status=status.HTTP_404_NOT_FOUND)   
                return CivilResponse({"message": "OTP sent to your email."}, status=status.HTTP_200_OK, is_success="OTP sent")
            except User.DoesNotExist:
                return CivilErrorResponse({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)
        return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(email=serializer.validated_data["email"])
            user.set_password(serializer.validated_data["new_password"])
            user.reset_token = None
            user.save()
            return CivilResponse({"message": "Password reset successful."}, status=status.HTTP_200_OK, is_success="Password changed")
        return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import JSONParser

class AdminProfileAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser]

    def get(self, request, format=None):
        """
        Retrieve the authenticated admin profile.
        """
        try:
            admin_user = request.user
            serializer = AdminProfileSerializer(admin_user)
            return CivilResponse(serializer.data, status=status.HTTP_200_OK, is_success="Admin profile retrieved successfully")
        except Exception as e:
            return CivilErrorResponse(str(e), status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, format=None):
        """
        Update the authenticated admin profile.
        """
        try:
            admin_user = request.user
            serializer = AdminProfileSerializer(admin_user, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return CivilResponse(serializer.data, status=status.HTTP_200_OK, is_success="Admin profile updated successfully")
            return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return CivilErrorResponse(str(e), status=status.HTTP_400_BAD_REQUEST)
