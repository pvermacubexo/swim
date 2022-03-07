import datetime
from django.core.mail import send_mail
from Appointment.models import Appointment
from SharkDeck import settings
from SharkDeck.celery import app

from celery import Celery

from user.models import User

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
    today_appointment = Appointment.objects.filter(start_time__day=datetime.datetime.now().day)

    today_date = datetime.datetime.now().date()
    instructor_list = []
    time_slot = {}
    subject = "Today's Appointment"
    for detail in today_appointment:
        instructor_id = detail.booking.class_instructor.instructor.id
        if instructor_id not in instructor_list:
            instructor_list.append(instructor_id)

    if not instructor_list:
        print("no have any appointment")
    else:
        for inst_list in instructor_list:
            today_appointment = Appointment.objects.filter(
                booking__class_instructor__instructor=inst_list,
                start_time__day=datetime.datetime.now().day)
            user_slot = {}
            for appoint in today_appointment:
                if instructor_list:
                    start_time = appoint.start_time.time().strftime("%H:%M")
                    end_time = appoint.end_time.time().strftime("%H:%M")
                    user_slot[start_time] = end_time
            time_slot[inst_list] = user_slot

    for i in instructor_list:
        print('i', i)
        instructor = User.objects.filter(id=i)
        for j in instructor:
            name = j.get_full_name()
            email = j.email
            time = time_slot.get(i)
            str_slot = ""
            for key, value in time.items():
                str_slot = str_slot + key + " to " + value + ",\n"
            email_body = f"hello {name},\n\nThis mail notify you that your today's {today_date} appointment is : \n" \
                         f"{str_slot}\n" \
                         f"Thank You,\n" \
                         f"Swim Time Solutions"
            try:
                send_mail(subject, email_body, settings.EMAIL_HOST_USER, [email])
            except Exception as e:
                return e



# def send_mail_body():
#     """ make email body of instructor's today available time slots"""
#     appoint = Appointment.objects.filter(start_time__day=datetime.datetime.now().day)
#     today_date = datetime.datetime.now()
#     count = 0
#     instructor_list = []
#     time_slot = {}
#     for detail in appoint:
#         instrct = detail.booking.class_instructor.instructor.id
#         print('hii', instrct)
#         if instrct not in instructor_list:
#             instructor_list.append(instrct)
#             today_slot = Appointment.objects.filter(
#                 booking__class_instructor__instructor=instructor_list[count],
#                 start_time__day=datetime.datetime.now().day)
#             count += 1
#
#             for appoint in today_slot:
#                 start_time = appoint.start_time.time().strftime("%H:%M")
#                 end_time = appoint.end_time.time().strftime("%H:%M")
#
#                 print({start_time: end_time})
#                 time_slot[start_time] = end_time
#                 # time_slot.update(start_time, end_time)
#     time_slot = time_slot
#     email_body = f"hello,\n \nThis mail notify you that your tomorrows {today_date} appointments time slot is " \
#                  f"start time {time_slot.keys()} - end time {time_slot.values()}\n\n" \
#                  f"Thank You,\nTeam Swim Time Solutions"
#     return email_body

# celery -A SharkDeck worker -l info
# celery -A SharkDeck beat -l info
