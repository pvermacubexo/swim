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
    slot_classes = []
    subject = "Appointment Reminder - Swim Time Solutions"
    for detail in today_appointment:
        instructor_id = detail.booking.class_instructor.instructor.id
        slot_classes.append(detail.booking.class_instructor.title)
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

    slot_class = slot_classes.__iter__()
    for i in instructor_list:
        instructor = User.objects.filter(id=i)
        for j in instructor:
            name = j.get_full_name()
            email = j.email
            time = time_slot.get(i)
            str_slot = ""
            for key, value in time.items():
                class_name = slot_class.__next__()
                str_slot = str_slot + class_name + " - " + key + " to " + value + ",\n"
            email_body = f"Hello {name},\n\nHope you are doing well. This mail is to remind you about your today's" \
                         f" appointment.\nPlease find below the details:\n" \
                         f"{str_slot}\n" \
                         f"Thank You,\n" \
                         f"Team Swim Time Solutions"
            try:
                send_mail(subject, email_body, settings.EMAIL_HOST_USER, [email])
            except Exception as e:
                return e

# celery -A SharkDeck worker -l info
# celery -A SharkDeck beat -l info
