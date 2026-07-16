from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from utils.response_utils import CivilResponse, CivilErrorResponse
from rest_framework import status
from django.shortcuts import get_object_or_404
from db.models import Project
from .serializers import *
from notification.views import TaskNotifier

class ProjectAPIView(APIView):
    serializer_class = ProjectSerializer

    def get(self, request, format=None):
        """
        Retrieve all projects.
        """
        try:
            projects = Project.objects.all()
            serializer = self.serializer_class(projects, many=True)
            return CivilResponse(serializer.data, status=status.HTTP_200_OK, is_success="Projects retrieved successfully")
        except Exception as e:
            return CivilErrorResponse(str(e), status=status.HTTP_400_BAD_REQUEST, resp_data=[])

    def post(self, request, format=None):
        """
        Create a new project.
        """
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return CivilResponse(serializer.data, status=status.HTTP_201_CREATED, is_success="Project created successfully")
            else:
                return CivilErrorResponse(error_message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return CivilErrorResponse(error_message=str(e), status=status.HTTP_400_BAD_REQUEST, resp_data=[])

class ProjectDetailAPIView(APIView):
    serializer_class = ProjectSerializer

    def get_object(self, project_id):
        """
        Retrieve a project instance.
        """
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return None

    def get(self, request, project_id, format=None):
        """
        Retrieve a single project by ID.
        """
        project = self.get_object(project_id)
        if not project:
            return CivilErrorResponse(error_message="Project not found", status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(project)
        return CivilResponse(serializer.data, status=status.HTTP_200_OK, is_success="Project retrieved successfully")

    def put(self, request, project_id, format=None):
        """
        Update an existing project.
        """
        project = self.get_object(project_id)
        if not project:
            return CivilErrorResponse(error_message="Project not found", status=status.HTTP_404_NOT_FOUND)

        try:
            serializer = self.serializer_class(project, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return CivilResponse(serializer.data, status=status.HTTP_200_OK, is_success="Project updated successfully")
            else:
                return CivilErrorResponse(error_message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return CivilErrorResponse(error_message=str(e), status=status.HTTP_400_BAD_REQUEST, resp_data=[])

    def delete(self, request, project_id, format=None):
        """
        Delete a project.
        """
        project = self.get_object(project_id)
        if not project:
            return CivilErrorResponse(error_message="Project not found", status=status.HTTP_404_NOT_FOUND)

        try:
            project.delete()
            return CivilResponse({}, status=status.HTTP_204_NO_CONTENT, is_success="Project deleted successfully")
        except Exception as e:
            return CivilErrorResponse(error_message=str(e), status=status.HTTP_400_BAD_REQUEST, resp_data=[])


class TaskListCreateAPIView(APIView):
    def get(self, request):
        tasks = Task.objects.all().order_by('-created_at')
        serializer = TaskDetailSerializer(tasks, many=True)
        return CivilResponse(serializer.data, status=status.HTTP_200_OK, is_success="Tasks retrieved successfully")


    def post(self, request):
        serializer = TaskDetailSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save()

            # Notify user
            notifier = TaskNotifier(task)
            notifier.notify()

            return CivilResponse(serializer.data, status=status.HTTP_201_CREATED, is_success="Task Created successfully")
        return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# Retrieve, update, delete a single task
class TaskDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Task, pk=pk)

    def get(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskDetailSerializer(task)
        return CivilResponse(serializer.data,status=status.HTTP_200_OK,is_success="Task retrieved successfully")

    def put(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskDetailSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()

            notifier = TaskNotifier(task)
            notifier.notify()

            return CivilResponse(serializer.data, status=status.HTTP_200_OK,is_success="Task Updated successfully")
        return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskDetailSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CivilResponse(serializer.data, status=status.HTTP_200_OK,is_success="Task Updated successfully")
        return CivilErrorResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        task = self.get_object(pk)
        task.delete()
        return CivilResponse(status=status.HTTP_204_NO_CONTENT,is_success="Task deleted successfully")
    

class DashboardSummaryAPIView(APIView):
    def get(self, request, format=None):
        """
        Retrieve summary of projects and tasks.
        """
        try:
            project_summary = {
                "total": Project.objects.count(),
                "new": Project.objects.filter(status="planning").count(),
                "ongoing": Project.objects.filter(status="on going").count(),
                "on_hold": Project.objects.filter(status="on hold").count(),
                "completed": Project.objects.filter(status="completed").count(),
            }

            task_summary = {
                "total": Task.objects.count(),
                "new": Task.objects.filter(status="planning").count(),
                "ongoing": Task.objects.filter(status="on going").count(),
                "on_hold": Task.objects.filter(status="on hold").count(),
                "completed": Task.objects.filter(status="completed").count(),
            }

            summary_data = {
                "projects": project_summary,
                "tasks": task_summary
            }
        
            serializer = DashboardSummarySerializer(summary_data)
        
            return CivilResponse(serializer.data, status=status.HTTP_200_OK, is_success="Dashboard summary retrieved successfully")

        except Exception as e:
            return CivilErrorResponse(error_message=str(e), status=status.HTTP_400_BAD_REQUEST)