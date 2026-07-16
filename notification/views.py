from django.core.mail import send_mail
from django.conf import settings
import requests

class TaskNotifier:
    def __init__(self, task):
        self.task = task
        self.user = task.assigned_to

    def notify(self):
        try:
            if not self.user:
                print("No user assigned to the task.")
                return

            if not getattr(self.user, 'notification', False):
                print(f"User {self.user} has notifications disabled.")
                return

            self.send_email()
            self.send_whatsapp()
        except Exception as e:
            print(f"[Notify Exception] {e}")

    def send_email(self):
        try:
            if not self.user.email:
                print("No email found for user.")
                return

            subject = "Task Update (CIVIL AI)"
            message = f"""
Hi {self.user.full_name},

Please find your task updates:

Title: {self.task.title}
Status: {self.task.status}
Priority: {self.task.priority}
Description: {self.task.description}
Due Date: {self.task.due_date}

Please take necessary action.

Best Regards,
Civil AI System.
"""
            send_mail(
                subject=subject.strip(),
                message=message.strip(),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[self.user.email],
                fail_silently=False,
            )
            print("Email sent successfully.")
        except Exception as e:
            print(f"[Email Exception] {e}")

    def send_whatsapp(self):
        try:
            if not self.user.phone:
                print("No phone number found for user.")
                return

            phone_number_id = settings.META_PHONE_NUMBER_ID
            access_token = settings.META_ACCESS_TOKEN
            url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": f"91{self.user.phone}",
                "type": "template",
                "template": {
                    "name": "task_update",  # or your custom approved template name
                    "language": { "code": "en_US" }
                }
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"[Meta WhatsApp Error] Status: {response.status_code}, Response: {response.text}")
            else:
                print("WhatsApp template message sent successfully via Meta API.")
                print(response.json())
        except Exception as e:
            print(f"[Meta WhatsApp Exception] {e}")
