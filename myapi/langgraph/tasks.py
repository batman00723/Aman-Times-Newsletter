from celery import shared_task
from django.core.mail import EmailMessage, get_connection
from backend.config import settings

@shared_task(bind=True, max_retries=3)
def send_newsletter_task(self, html_content, recipients):
    try:
        connection = get_connection(fail_silently=False)
        email = EmailMessage(
            subject="Geopolitics Digest Daily: Morning Briefing",
            body=html_content,
            from_email=settings.email_host_user,
            to=["amanmishrarewa23@gmail.com"],
            bcc=recipients,
            connection=connection
        )
        email.content_subtype = "html"
        return email.send()
    except Exception as exc:
        # If the SMTP server is down, Celery will retry automatically
        raise self.retry(exc=exc, countdown=60)