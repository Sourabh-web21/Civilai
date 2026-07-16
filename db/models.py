
from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager as AbstractUserManager

class UserManager(AbstractUserManager):
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError("The email is required")
        user = self.model(email=email, **extra_fields)
        user.is_active =True
        user.set_password(password)
        user.save()
        return user


    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)


        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)

ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        # ('engineer', 'Engineer'),
        # ('worker', 'Worker'),
        ('client', 'Client'),
    )

class User(AbstractUser):
    username= models.CharField(max_length=30, unique=False)
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=10,blank=True,null=True, unique=True)
    email = models.EmailField(max_length=200, unique=True, db_index=True)
    image = models.ImageField(upload_to='media', max_length=255, null=True, blank=True,default=None)
    role = models.CharField(max_length=20,choices=ROLE_CHOICES,blank=True,default="manager")
    notification = models.BooleanField(default=True, null=True, blank=True)

    reset_token = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    AbstractUser._meta.get_field('email')._unique = True
    objects = UserManager()

    class Meta:
        db_table = 'users'


    def __str__(self):
        return self.email



class Project(models.Model):
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('on going', 'On Going'),
        ('on hold', 'On Hold'),
        ('completed', 'Completed'),
    )
    name = models.CharField(max_length=255)
    sanction_date = models.DateField()
    length_km = models.FloatField()
    total_project_cost = models.DecimalField(max_digits=10, decimal_places=2)
    lane_configuration = models.CharField(max_length=100)
    contractor_name = models.CharField(max_length=255)
    tender_amount = models.DecimalField(max_digits=10, decimal_places=2)
    completion_period_months = models.IntegerField()
    appointed_date = models.DateField()
    scheduled_completion_date = models.DateField()
    total_delay_days = models.IntegerField(null=True, blank=True)
    physical_progress = models.FloatField()
    financial_progress = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    # budget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'projects'


class ProjectEOT(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='eots')
    eot_date = models.DateField()
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"EOT for {self.project.name} on {self.eot_date}"

    class Meta:
        db_table = 'project_eots'


class ProjectRevisedCost(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='revised_costs')
    revised_cost = models.DecimalField(max_digits=10, decimal_places=2)
    revision_date = models.DateField()
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Revised Cost for {self.project.name}: {self.revised_cost}"

    class Meta:
        db_table = 'project_revised_costs'


class ProjectMilestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    milestone_name = models.CharField(max_length=255)  # e.g., Milestone-I, Milestone-II
    due_date = models.DateField()  # Expected completion date
    days_from_appointed = models.IntegerField()  # Days from appointed date
    expenditure_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # % of project cost

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.milestone_name}"

    class Meta:
        db_table = "project_milestones"
        ordering = ["due_date"]

#  Task Priorities
class Task(models.Model):
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('on going', 'On Going'),
        ('on hold', 'On Hold'),
        ('completed', 'Completed'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE,null=True,blank=True, related_name="tasks")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.project.name}"
    
    class Meta:
        db_table = 'tasks'
        
# Task Notes (Comments on Tasks)
class TaskNote(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="notes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_notes")
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note by {self.user.username} on {self.task.title}"
    
    class Meta:
        db_table = 'task_notes'

# Task Attachments (Files)
class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="files")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_files")
    file = models.FileField(upload_to="task_files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"File for {self.task.title} by {self.uploaded_by.username}"

    class Meta:
        db_table = 'task_files'

# Task Updates (Task Progress Updates)
class TaskUpdate(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="updates")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_updates")
    # status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Update for {self.task.title} by {self.updated_by.username}"

#  Activity Log (Logs for Task & Project Activities)
# class ActivityLog(models.Model):
#     ACTION_CHOICES = (
#         ('created', 'Created'),
#         ('updated', 'Updated'),
#         ('deleted', 'Deleted'),
#         ('status_changed', 'Status Changed'),
#     )
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_logs")
#     project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="activity_logs", blank=True, null=True)
#     task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activity_logs", blank=True, null=True)
#     action = models.CharField(max_length=50, choices=ACTION_CHOICES)
#     description = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user.username} - {self.action}"

