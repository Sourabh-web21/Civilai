# # run_queries.py
# import os
# import django

# # Set up Django environment
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'construction_ai.settings')
# django.setup()

# # Import your models
# from db.models import *


# #CREATE PROJECT
# obj  = Project.objects.create(name = "NH30", sanction_date = "2025-04-15", length_km = 30.00,
#                                total_project_cost=85.300, lane_configuration= "2 lane", contractor_name = "NTPC",
#                                tender_amount = 90,completion_period_months=23, appointed_date = "2025-04-15",
#                                scheduled_completion_date = "2025-04-15",total_delay_days = 56, physical_progress = 78,
#                                financial_progress = 68 )

# obj.save()


# # Run ORM queries
# queryset =Project.objects.all()
# # Task.objects.select_related('project', 'assigned_to')

# for object in queryset:
#     print(object.name)
