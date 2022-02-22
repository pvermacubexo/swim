import datetime
from django.core.mail import send_mail
from Appointment.models import Appointment
from SharkDeck import settings
from SharkDeck.celery import app

from celery import Celery

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_ENABLE_UTC = False


# app = Celery('tasks', broker='pyamqp://guest@localhost//')


@app.task
def sent_mail_task(*args, **kwargs):
    """ this task help to send mail. """
    try:
        send_mail(kwargs['subject'], kwargs['email_body'], settings.EMAIL_HOST_USER, [kwargs['user_email']])
    except Exception as msg:
        raise msg
    return "Sent_mail_task done"


@app.task
def appointment_mail():
    get_appointment = Appointment.objects.all()
    # now = datetime.datetime.utcnow()  # 2022-02-21 09:52:55.618620
    # now = datetime.datetime.now()       #2022-02-21 09:55:09.027564
    # get_detail = [i.start_time for i in get_appointment]
    # print(get_detail)
    # get_detail = [appoint for appoint in get_appointment]
    # print(type(get_detail))
    # print(get_detail[:])
    for appointment in get_appointment:
        # users_email = [appointment.booking.user.email]
        user_name = appointment.booking.user.get_full_name()
        date = appointment.start_time.date()  # 2022-02-19 07:46:00+00:00
        start_time = appointment.start_time.time()
        end_time = appointment.end_time.time()
        # print(type(appointment.start_time.date()))

        subject = f"Today's Appointments"
        email_body = f"hello {user_name},\n \nThis mail notify you that your tomorrows {date}appointments time slot is " \
                     f"start time {start_time} - end time {end_time}\n\n" \
                     f"Thank You,\nTeam Swim Time Solutions"
        print("message send")
    try:
        send_mail(subject, email_body, settings.EMAIL_HOST_USER, ['dinesh.parihar@cubexo.io'])
    except Exception as e:
        pass


# def send_mail_body():
#     get_appointment = Appointment.objects.all()
#     for appointment in get_appointment:
#         now = datetime.datetime.now()  # 2022-02-22 09:55:09.027564
#         # now = datetime.datetime.now().now()  # 2022-02-22
#         date = appointment.start_time  # 2022-02-19 07:46:00+00:00
#         date = appointment.start_time.date()  # 2022-02-18
#         appoint_date = appointment.start_time.date()
#
#         if appoint_date == now:
#             today_appointment = Appointment.objects.filter(start_time__gte=now)
#         users_email = [appointment.booking.user.email]
#         user_name = appointment.booking.user.get_full_name()
#         date = appointment.start_time.date()
#         start_time = appointment.start_time.time()
#         end_time = appointment.end_time.time()
#
#         subject = f"Today's Appointments"
#         email_body = f"hello {user_name},\n \nThis mail notify you that your tomorrows {date}appointments time slot is " \
#                      f"start time {start_time} - end time {end_time}\n\n" \
#                      f"Thank You,\nTeam Swim Time Solutions"
#         return email_body

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
