import datetime
from django.core.mail import send_mail
from Appointment.models import Appointment
from SharkDeck import settings
from SharkDeck.celery import app


@app.task
def appointment_mail():
    get_appointment = Appointment.objects.all()
    # now = datetime.datetime.utcnow()  # 2022-02-21 09:52:55.618620
    # now = datetime.datetime.now()       #2022-02-21 09:55:09.027564
    get_detail = [i.start_time for i in get_appointment]
    print(get_detail)
    for appointment in get_appointment:
        users_email = [appointment.booking.user.email]
        user_name = appointment.booking.user.get_full_name()
        date = appointment.start_time.date()
        start_time = appointment.start_time.time()
        end_time = appointment.end_time.time()

        subject = f"Tomorrow Appointments"
        email_body = f"hello {user_name},\n \nThis mail notify you that your tomorrows {date}appointments time slot is " \
                     f"start time {start_time} - end time {end_time}\n\n" \
                     f"Thank You,\nTeam Swim Time Solutions"
        print("message send")
        try:
            send_mail(subject, email_body, settings.EMAIL_HOST_USER, ['dinesh.parihar@cubexo.io'])
        except Exception as e:
            pass
    # for appointment in get_appointment:
    #     date = appointment.start_time.date()
    #     # if date == now:
    #     send_mail("this is subject", "this is email body", settings.EMAIL_HOST_USER, ['dinesh.parihar@cubexo.io'])

# @app.task
# def check():
#     import requests
#
#     url = "https://webhook.site/6e83818d-a1d3-4759-85da-1e813ab44e80"
#
#     payload = {}
#     headers = {}
#
#     response = requests.request("GET", url, headers=headers, data=payload)
#     print("Checklojgm")

# from celery import Celery
#
# app = Celery('tasks', broker='redis://localhost:6379/0')
#
#
# @app.task
# def check():
#     print('I am checking your stuff')
#
#
# app.conf.beat_schedule = {
#     'run-me-every-ten-seconds': {
#         'task': 'tasks.check',
#         'schedule': 10.0
#     }
# }

# import datetime
# from django.utils.timezone import utc
# from celery import Celery, shared_task
# from SharkDeck import settings
# from django.core.mail import send_mail
# from celery.schedules import crontab
# from celery.schedules import schedule
# from Appointment.models import Appointment, Booking
# # from app.email_notification import mail_notification
# from celery.utils.log import get_task_logger
#
# app = Celery('SharkDeck', broker='pyamqp://guest@localhost//')
#
#
# # @app.task
# # def sent_mail_task(*args, **kwargs):
# #     """ this task help to send mail. """
# #     try:
# #         send_mail(kwargs['subject'], kwargs['email_body'], settings.EMAIL_HOST_USER, [kwargs['user_email']])
# #     except Exception as msg:
# #         raise msg
# #     return "Sent_mail_task done"
#
#
# @shared_task()
# def appointment_mail():
#     import requests
#
#     url = "https://webhook.site/6e83818d-a1d3-4759-85da-1e813ab44e80"
#
#     payload = {}
#     headers = {}
#
#     response = requests.request("GET", url, headers=headers, data=payload)
#     get_appointment = Appointment.objects.all()
#     now = datetime.datetime.utcnow()  # 2022-02-21 09:52:55.618620
#     # now = datetime.datetime.now()       #2022-02-21 09:55:09.027564
#     get_detail = [i.start_time for i in get_appointment]
#     print(get_detail)
#     for appointment in get_appointment:
#         date = appointment.start_time.date()
#         # if date == now:
#         send_mail("this is subject", "this is email body", settings.EMAIL_HOST_USER, ['dinesh.parihar@cubexo.io'])
#
#
# # crontab(hour=7, minute=30, day_of_week=1)
# # sender.add_periodic_task(
# #         crontab(hour=7, minute=30, day_of_week=1),
# #         test.s('Happy Mondays!'),
# #     )
#
