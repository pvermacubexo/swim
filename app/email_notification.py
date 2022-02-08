from django.core.mail import send_mail
from SharkDeck import settings
from django.contrib import messages


def mail_notification(request, subject, email_body, user_email):
    """ user email notification """
    sent = send_mail(subject, email_body, settings.EMAIL_HOST_USER, [user_email])
    return sent
