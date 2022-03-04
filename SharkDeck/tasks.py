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
    for appointment in get_appointment:
        # users_email = [appointment.booking.user.email]
        user_name = appointment.booking.user.get_full_name()
        date = appointment.start_time.date()  # 2022-02-19 07:46:00+00:00
        start_time = appointment.start_time.time()
        end_time = appointment.end_time.time()

        subject = f"Today's Appointments"
        email_body = f"hello {user_name},\n \nThis mail notify you that your tomorrows {date}appointments time slot is " \
                     f"start time {start_time} - end time {end_time}\n\n" \
                     f"Thank You,\nTeam Swim Time Solutions"
        print("message send")
    try:
        email_body = send_mail_body()
        send_mail(subject, email_body, settings.EMAIL_HOST_USER, ['dinesh.parihar@cubexo.io'])
    except Exception as e:
        pass


def send_mail_body():
    """ make email body of instructor's today available time slots"""
    appoint = Appointment.objects.filter(start_time__day=datetime.datetime.now().day)
    today_date = datetime.datetime.now()
    count = 0
    instructor_list = []
    time_slot = {}
    for detail in appoint:
        instrct = detail.booking.class_instructor.instructor.id
        print('hii', instrct)
        if instrct not in instructor_list:
            instructor_list.append(instrct)
            today_slot = Appointment.objects.filter(
                booking__class_instructor__instructor=instructor_list[count],
                start_time__day=datetime.datetime.now().day)
            count += 1

            for appoint in today_slot:
                start_time = appoint.start_time.time().strftime("%H:%M")
                end_time = appoint.end_time.time().strftime("%H:%M")

                print({start_time: end_time})
                time_slot[start_time] = end_time
                # time_slot.update(start_time, end_time)
    time_slot = time_slot
    email_body = f"hello,\n \nThis mail notify you that your tomorrows {today_date} appointments time slot is " \
                 f"start time {time_slot.keys()} - end time {time_slot.values()}\n\n" \
                 f"Thank You,\nTeam Swim Time Solutions"
    return email_body

# datetime.now().strftime("%Y-%m-%d, %H:%M"))
# appointments = appointment_model.Appointment.objects.filter(booking__class_instructor__instructor=request.user)
#     today_appointment = appointment_model.Appointment.objects.filter(start_time__day=datetime.now().day)
#
#     today_date = datetime.now()
#     count = 0
#     instructor_list = []
#     time_slot = {}
#     add = 0
#     subject = "Today's Appointment"
#     for detail in today_appointment:
#         instructor_id = detail.booking.class_instructor.instructor.id
#         if instructor_id not in instructor_list:
#             instructor_list.append(instructor_id)
#             print('hii', instructor_id)
#             today_slot = appointment_model.Appointment.objects.filter(
#                 booking__class_instructor__instructor=instructor_list[count],
#                 start_time__day=datetime.now().day)
#             count += 1
#             for appoint in today_slot:
#                 start_time = appoint.start_time.time().strftime("%H:%M")
#                 end_time = appoint.end_time.time().strftime("%H:%M")
#                 print({start_time: end_time})
#                 time_slot[start_time] = end_time
#         time_slot = time_slot
#         var = f"start time, {time_slot.keys()} end time {time_slot.values()}"
#         email_body = f"hello ,\nThis mail notify you that your tomorrows {today_date.date()} appointments time slot is " \
#                      f"{var}\n" \
#                      f"Thank You"
#
#         print(email_body)

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

# celery -A SharkDeck worker -l info
# celery -A SharkDeck beat -l info
