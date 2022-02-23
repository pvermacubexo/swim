import datetime
from django.utils.timezone import utc
from celery import Celery, shared_task
from SharkDeck import settings
from django.core.mail import send_mail
from celery.schedules import crontab
from celery.schedules import schedule
# from app.email_notification import mail_notification
from celery.utils.log import get_task_logger

app = Celery('tasks', broker='pyamqp://guest@localhost//')


@app.task
def sent_mail_task(*args, **kwargs):
    """ this task help to send mail. """
    try:
        send_mail(kwargs['subject'], kwargs['email_body'], settings.EMAIL_HOST_USER, [kwargs['user_email']])
    except Exception as msg:
        raise msg
    return "Sent_mail_task done"

#
# @shared_task()
# def appointment_mail():
#     get_appointment = Appointment.objects.all()
#     now = datetime.datetime.utcnow()  # 2022-02-21 09:52:55.618620
#     # now = datetime.datetime.now()       #2022-02-21 09:55:09.027564
#     for appointment in get_appointment:
#         date = appointment.start_time.date()
#         if date == now:
#             send_mail("this is subject", "this is email body", settings.EMAIL_HOST_USER, ['dinesh.parihar@cubexo.io'])

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
