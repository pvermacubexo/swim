from django.conf import settings
from celery import Celery
from SharkDeck import settings
from django.core.mail import send_mail
# from app.email_notification import mail_notification
from celery.utils.log import get_task_logger

app = Celery('tasks', broker='pyamqp://guest@localhost//')


# def mail_notification(*args, **kwargs):
#     """ user email notification """
#     sent = send_mail(kwargs['subject'], kwargs['email_body'], settings.EMAIL_HOST_USER, [kwargs['user_email']])
#     return sent


@app.task
def sent_mail_task(*args, **kwargs):
    """ this task help to send mail. """
    try:
        send_mail(kwargs['subject'], kwargs['email_body'], settings.EMAIL_HOST_USER, [kwargs['user_email']])
    except Exception as msg:
        raise msg
        # print("task not done", msg)
    return "Sent_mail_task done"

    # sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
    #                                    'user_email': user_email})

# @app.send_task()
# def sent_mail_task(*args, **kwargs):
#     """ this task help to send mail. """
#     send_mail(kwargs['subject'], kwargs['email_body'], settings.EMAIL_HOST_USER, [kwargs['user_email']])
#     return 'first_task_done'

# crontab(hour=7, minute=30, day_of_week=1)
# sender.add_periodic_task(
#         crontab(hour=7, minute=30, day_of_week=1),
#         test.s('Happy Mondays!'),
#     )

# @app.task
# def sent_mail_task(*args, **kwargs):
#     """ this task help to send mail. """
#     subject = kwargs['subject']
#     print('subject', subject)
#
#     mail_notification(subject=kwargs['subject'], email_body=kwargs['email_body'], user_email=kwargs['user_email'])
#     return 'first_task_done'
