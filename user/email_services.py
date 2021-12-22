from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def sent_mail(data):
    subject = data['email_subject']
    to = [data['to_email']]
    text_content = 'This is an important message.'
    html_content = data['email_body']
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()