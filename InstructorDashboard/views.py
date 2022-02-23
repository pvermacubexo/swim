import logging
import os
from datetime import datetime, timedelta, date
from random import randint

import pytz
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import DetailView

from Appointment import models as appointment_model
from Appointment import utilities
from Appointment.models import ClassInstructor, APPOINTMENT_STATUS
from SharkDeck.constants import user_constants
from StripePayment.models import StripeAccount
from app.email_notification import mail_notification
from user import models as user_models
from user.email_services import sent_mail
from . import seializer
from . import serializer, utility
from .forms import BreakTimeFormSet
from SharkDeck import settings
from SharkDeck.tasks import sent_mail_task

BASE_URL = settings.BASE_URL

logger = logging.getLogger(__name__)


def generate_slug(first_name, last_name):
    obj = len(user_models.Profile.objects.all())
    if user_models.Profile.objects.filter(slug=first_name).exists():
        if user_models.Profile.objects.filter(slug=first_name + last_name).exists():
            slug = (first_name + last_name + str(obj))
            return slug
        else:
            slug = (first_name + last_name)
            return slug
    else:
        slug = first_name
        return slug


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('InstructorDashboard:dashboard_view')

    context = {}
    if request.method == 'GET':
        return render(request, 'InstructorDashboard/auth/login.html')

    else:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        conf_password = request.POST.get('conf_password')
        mobile_no = request.POST.get('mobile_no')
        if user_models.User.objects.filter(email=email).exists():
            return render(request, 'InstructorDashboard/auth/login.html', {'error': 'email already exist.'})
        if int(len(password)) < 7:
            context.update({'error': 'Password must continent at-least 8 character.'})
            return render(request, 'InstructorDashboard/auth/login.html', context)

        if not (password == conf_password):
            context.update({'error': 'Password must equal.'})
            return render(request, 'InstructorDashboard/auth/login.html', context)
        slug = generate_slug(first_name, last_name)
        user = user_models.User.objects.create(email=email, first_name=first_name, last_name=last_name,
                                               password=make_password(password), mobile_no=mobile_no,
                                               user_type=user_constants.Instructor)

        user_name = user.get_full_name()
        subject = "Registration Successful - Swim Time Solutions"
        email_body = f"Hello {user_name},\n \nWelcome to Swim Time Solutions, " \
                     f"Your account is now set up and ready to use. Let's get started!\n\n" \
                     f"Thank You," \
                     f"\nSwim Time Solutions"
        try:
            sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                               'user_email': email})
        except Exception as e:
            pass

        logger.info(f"{user} created successfully.")
        front_end_url_local = os.environ.get("FRONT_END_URL_LOCAL")
        front_end_url = os.environ.get("FRONT_END_URL")
        if user:
            date_time = datetime.now()
            time_added = date_time + timedelta(minutes=1)
            user_profile = user_models.Profile.objects.create(
                user=user,
                slug=slug,
                url=(BASE_URL + '/swim/instructor/' + slug).replace(' ', ''),
                day_start_time=date_time.time(),
                day_end_time=time_added.time()
            )
            logger.info(f"{user_profile} profile successfully.")
            auth_user = authenticate(email=user.email, password=password)
            if auth_user:
                logger.info(f"{auth_user} is authorized successfully.")
                login(request, auth_user)
                logger.info(f"{auth_user} login successfully.")
                # return render(request, 'InstructorDashboard/instructor_profile.html', {'instructor': user_profile})
                return redirect('InstructorDashboard:instructor_profile')
        logger.info(f"{user.email} is not authorized with this credential.")
        return render(request, 'InstructorDashboard/auth/login.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('InstructorDashboard:dashboard_view')

    context = {}
    if request.method == 'GET':
        return render(request, 'InstructorDashboard/auth/login.html')

    else:
        ser = serializer.LoginDataVerifier(data=request.POST)
        if not ser.is_valid():
            context.update({'errors': utility.serializer_error_to_dict(ser.errors)})
            return render(request, 'InstructorDashboard/auth/login.html', context=context)
        else:
            user = ser.get_user()
            if not user:
                context.update({'page_errors': ['Username or Password is incorrect.']})
                return render(request, 'InstructorDashboard/auth/login.html', context=context)
            if user.user_type == user_constants.Instructor:
                login(request, user)

                # user_email = request.POST['email']
                # hostname = socket.gethostname()
                # IPAddress = socket.gethostbyname(hostname)
                # subject = "Security Alert"
                # email_body = f"We noticed a new sign-in to your Swim Time Solutions Account on a device IP Address - {IPAddress} . If this was you, you don’t need to do anything. If not, please change your password to secure your account."
                # mail_notification(request, subject, email_body, user_email)

                return redirect('InstructorDashboard:dashboard_view')
            context.update({'page_errors': ['User does not have permission to access this portal.']})
            return render(request, 'InstructorDashboard/auth/login.html', context=context)


def user_logout(request):
    logger.info(f"{request.user} Successfully Logged out")
    logout(request)
    return redirect('InstructorDashboard:home')


def home_view(request):
    return render(request, "index.html")


@login_required(redirect_field_name='login')
def dashboard_view(request):
    if not request.user.user_type == user_constants.Instructor:
        return redirect('InstructorDashboard:user_logout')

    context = {}
    credit_amount = 0
    pending_amount = 0
    bookings = utilities.get_instructors_bookings(request.user)
    transactions = utilities.get_instructor_transactions(request.user)
    complete_transactions = utilities.get_complete_transactions(request.user)
    pending_transactions = utilities.get_pending_transactions(request.user)
    for complete_transaction in complete_transactions:
        credit_amount += complete_transaction.paid_amount
    for pending_transaction in pending_transactions:
        pending_amount += pending_transaction.paid_amount
    appointments = appointment_model.Appointment.objects.filter(booking__class_instructor__instructor=request.user,
                                                                start_time__day=datetime.now().day)
    context = {'appointments': appointments,
               'transactions': transactions,
               'total_bookings': bookings.count(),
               'total_students': len(set([booking.user for booking in bookings])),
               'credit_amount': credit_amount,
               'pending_transaction': pending_amount
               }
    return render(request, 'InstructorDashboard/dashboard.html', context=context)


@login_required(redirect_field_name='login')
def trainee_view(request, trainee):
    try:
        trainee = user_models.Kids.objects.get(id=trainee)
    except user_models.Kids.DoesNotExist:
        return redirect('InstructorDashboard:page404')
    transactions = appointment_model.Transaction.objects.filter(booking__kids=trainee).order_by('-payment_at')
    today = datetime.today().replace(tzinfo=pytz.UTC)
    bookings = appointment_model.Booking.objects.filter(kids=trainee).order_by("-booked_at")
    appointment_status_options = dict(APPOINTMENT_STATUS)
    context = {'trainee': trainee,
               'transactions': transactions, 'bookings': bookings,
               'today': today, 'appointment_status_options': appointment_status_options}
    return render(request, 'InstructorDashboard/profile.html', context=context)


@login_required(redirect_field_name='login')
def update_transaction(request, id):
    try:
        complete_amount = 0
        transaction = appointment_model.Transaction.objects.get(id=id)
        transaction.status = appointment_model.COMPLETED
        transaction.save()

        user_name = transaction.booking.user.get_full_name()
        transaction_amount = transaction.paid_amount
        user_email = transaction.booking.user.email
        subject = f"Cash Accepted - Swim Time Solutions"
        email_body = f"Dear {user_name},\n \nThis mail is regarding your cash payment approval. Your cash payment of" \
                     f" {transaction_amount} USD is accepted by the Instructor.\n\n" \
                     f"Thank You,\nTeam Swim Time Solutions"
        try:
            sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                               'user_email': user_email})
        except Exception as e:
            pass

        booking = appointment_model.Booking.objects.get(id=transaction.booking.id)
        transactions = appointment_model.Transaction.objects.filter(booking=transaction.booking,
                                                                    status=appointment_model.COMPLETED)
        for i in transactions:
            complete_amount += i.paid_amount
        if booking.class_instructor.price == complete_amount:
            booking.booking_payment_status = appointment_model.BOOKING_COMPLETED
            booking.save()
    except appointment_model.Transaction.DoesNotExist:
        return redirect('InstructorDashboard:page404')
    return redirect('InstructorDashboard:trainee_view', transaction.booking.kids.id)


@login_required(redirect_field_name='login')
def delete_transaction(request, id):
    try:
        transaction = appointment_model.Transaction.objects.get(id=id)
        transaction.status = appointment_model.REJECTED
        transaction.save()

        user_name = transaction.booking.user.get_full_name()
        transaction_amount = transaction.paid_amount
        user_email = transaction.booking.user.email
        subject = f"Cash Rejected  - Swim Time Solutions"
        email_body = f"Dear {user_name},\n \nThis mail is regarding your cash payment rejection. Your cash payment of" \
                     f" {transaction_amount} USD is rejected by the Instructor. You may contact the Instructor for further information.\n\n" \
                     f"Thank you,\nTeam Swim Time Solutions"
        try:
            sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                               'user_email': user_email})
        except Exception as e:
            pass

    except appointment_model.Transaction.DoesNotExist:
        return redirect('InstructorDashboard:page404')
    return redirect('InstructorDashboard:trainee_view', transaction.booking.kids.id)


@login_required(redirect_field_name='login')
def update_booking(request, id):
    if request.method == 'POST':
        data = request.POST

        if data:
            print(id)
            appointment_obj = appointment_model.Appointment.objects.get(id=int(data['id']))
            appointment_obj.remark = data['remark']
            appointment_obj.status = data['status']
            appointment_obj.save()

            if data['status'] == '3':
                user_name = appointment_obj.booking.user.get_full_name()
                kid_name = appointment_obj.booking.kids.kids_name
                user_email = appointment_obj.booking.user.email
                subject = "Appointment Cancelled - Swim Time Solutions"
                email_body = f"Hello {user_name},\n\nThis is to notify that your student name {kid_name} appointment of Date {appointment_obj.start_time.date()}, Time {appointment_obj.start_time.time()} to {appointment_obj.end_time.time()} reason of {data['remark']} has been cancelled.\n\n" \
                             f"Thank You,\n" \
                             f"Swim Time Solutions"
                try:
                    sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                                       'user_email': user_email})
                except Exception as e:
                    pass

            print("updated")

            # return render(request, 'InstructorDashboard/dashboard.html', context=context)
            return redirect("InstructorDashboard:trainee_view", id)

        else:

            return redirect("InstructorDashboard:trainee_view", id)

    return redirect("InstructorDashboard:trainee_view", id)


def check_appointment(start_time, end_time, day, instructor):
    appointments = appointment_model.Appointment.objects.filter(
        booking__class_instructor__instructor__id=instructor.user.id, start_time__week_day=day,
        status=appointment_model.SCHEDULED)
    for appointment in appointments:
        if (str(appointment.start_time.time()) <= start_time <= str(appointment.end_time.time())) and (
                str(appointment.start_time.time()) <= end_time <= str(appointment.end_time.time())):
            return False, f"You have already an appointment."

        if (str(appointment.start_time.time()) >= start_time <= str(appointment.end_time.time())) and (
                str(appointment.start_time.time()) <= end_time <= str(appointment.end_time.time())):
            return False, f"You have already an appointment."

        if (str(appointment.start_time.time()) <= start_time <= str(appointment.end_time.time())) and (
                str(appointment.end_time.time()) <= end_time):
            return False, f"You have already an appointment."

        if str(appointment.start_time.time()) >= start_time and str(appointment.end_time.time()) <= end_time:
            return False, f"You have already an appointment."

    return True, True


def week_settings(user_obj, week_dict):
    try:
        week_time = user_models.WeekTimeSlots.objects.get(instructor=user_obj)
    except user_models.WeekTimeSlots.DoesNotExist:
        week_time = None
    for k, v in week_dict.items():
        if bool(v['switch']):
            if k == 'monday':
                is_appointment = check_appointment(v['start'].replace(" ", ""), v['end'].replace(" ", ""), 2, user_obj)
                if not is_appointment[0]:
                    return is_appointment
                if week_time:
                    week_time.monday_startTime_slot = v['start'].replace(" ", "")
                    week_time.monday_endTime_slot = v['end'].replace(" ", "")

                else:
                    create = user_models.WeekTimeSlots.objects.create(
                        instructor=user_obj,
                        monday_startTime_slot=v['start'].replace(" ", ""),
                        monday_endTime_slot=v['end'].replace(" ", "")
                    )

            if k == 'tuesday':
                is_appointment = check_appointment(v['start'].replace(" ", ""), v['end'].replace(" ", ""), 3, user_obj)
                if not is_appointment[0]:
                    return is_appointment
                if week_time:
                    week_time.tuesday_startTime_slot = v['start'].replace(" ", "")
                    week_time.tuesday_endTime_slot = v['end'].replace(" ", "")

                else:
                    create = user_models.WeekTimeSlots.objects.create(
                        instructor=user_obj,
                        tuesday_startTime_slot=v['start'].replace(" ", ""),
                        tuesday_endTime_slot=v['end'].replace(" ", "")
                    )
            if k == 'wednesday':
                is_appointment = check_appointment(v['start'].replace(" ", ""), v['end'].replace(" ", ""), 4, user_obj)
                if not is_appointment[0]:
                    return is_appointment
                if week_time:
                    week_time.wednesday_startTime_slot = v['start'].replace(" ", "")
                    week_time.wednesday_endTime_slot = v['end'].replace(" ", "")

                else:
                    create = user_models.WeekTimeSlots.objects.create(
                        instructor=user_obj,
                        wednesday_startTime_slot=v['start'].replace(" ", ""),
                        wednesday_endTime_slot=v['end'].replace(" ", "")
                    )
            if k == 'thursday':
                is_appointment = check_appointment(v['start'].replace(" ", ""), v['end'].replace(" ", ""), 5, user_obj)
                if not is_appointment[0]:
                    return is_appointment
                if week_time:
                    week_time.thursday_startTime_slot = v['start'].replace(" ", "")
                    week_time.thursday_endTime_slot = v['end'].replace(" ", "")

                else:
                    create = user_models.WeekTimeSlots.objects.create(
                        instructor=user_obj,
                        thusday_startTime_slot=v['start'].replace(" ", ""),
                        thusday_endTime_slot=v['end'].replace(" ", "")
                    )
            if k == 'friday':
                is_appointment = check_appointment(v['start'].replace(" ", ""), v['end'].replace(" ", ""), 6, user_obj)
                if not is_appointment[0]:
                    return is_appointment
                if week_time:
                    week_time.friday_startTime_slot = v['start'].replace(" ", "")
                    week_time.friday_endTime_slot = v['end'].replace(" ", "")

                else:
                    create = user_models.WeekTimeSlots.objects.create(
                        instructor=user_obj,
                        friday_startTime_slot=v['start'].replace(" ", ""),
                        friday_endTime_slot=v['end'].replace(" ", "")
                    )
            if k == 'saturday':
                is_appointment = check_appointment(v['start'].replace(" ", ""), v['end'].replace(" ", ""), 7, user_obj)
                if not is_appointment[0]:
                    return is_appointment
                if week_time:
                    week_time.saturday_startTime_slot = v['start'].replace(" ", "")
                    week_time.saturday_endTime_slot = v['end'].replace(" ", "")

                else:
                    create = user_models.WeekTimeSlots.objects.create(
                        instructor=user_obj,
                        saturday_startTime_slot=v['start'].replace(" ", ""),
                        saturday_endTime_slot=v['end'].replace(" ", "")
                    )

            if k == 'sunday':
                is_appointment = check_appointment(v['start'].replace(" ", ""), v['end'].replace(" ", ""), 1, user_obj)
                if not is_appointment[0]:
                    return is_appointment
                if week_time:
                    week_time.sunday_startTime_slot = v['start'].replace(" ", "")
                    week_time.sunday_endTime_slot = v['end'].replace(" ", "")

                else:
                    create = user_models.WeekTimeSlots.objects.create(
                        instructor=user_obj,
                        sunday_startTime_slot=v['start'].replace(" ", ""),
                        sunday_endTime_slot=v['end'].replace(" ", "")
                    )
    user_obj.save()
    week_time.save()
    return True, True


def is_working_time(start_time, end_time, instructor):
    start_time = str(start_time)
    appointments = appointment_model.Appointment.objects.filter(booking__class_instructor__instructor=instructor,
                                                                start_time__gte=datetime.now())
    for appointment in appointments:
        if (str(appointment.start_time.time()) <= start_time <= str(appointment.end_time.time())) or (
                str(appointment.start_time.time()) <= end_time <= str(appointment.end_time.time())):
            return False, "You have appointment(s)"
    return True, True


@login_required(redirect_field_name='login')
def instructor_profile(request):
    request.session["instructor_email"] = request.user.email
    formset = BreakTimeFormSet(queryset=user_models.BreakTime.objects.none())
    break_time_list = user_models.BreakTime.objects.filter(instructor__user=request.user)
    try:
        instructor = user_models.User.objects.get(id=request.user.id)
        user = user_models.Profile.objects.get(user=request.user)
    except user_models.User.DoesNotExist:
        return redirect('InstructorDashboard:page404')
    except user_models.Profile.DoesNotExist:
        return redirect('InstructorDashboard:page404')
    context = {'instructor': instructor, 'break_time': formset, 'break_time_list': break_time_list,
               'instructor_id': user.id}
    if StripeAccount.objects.filter(Instructor__email=request.user.email).exists():
        context.update({"stripe_account": StripeAccount.objects.filter(
            Instructor__email=request.user.email).values("Account_ID", "Instructor__email",
                                                         "Instructor__first_name", "Instructor__last_name")[0]})
    if request.method == 'POST':
        week_dict = {}
        ser = serializer.UserUpdateSerializer(data=request.POST)
        if not ser.is_valid():
            context.update({'errors': utility.serializer_error_to_dict(ser.errors)})
            return render(request, 'InstructorDashboard/instructor_profile.html', context)
        start_time = request.POST.get('day_start_time')
        end_time = request.POST.get('day_end_time')
        working_time = is_working_time(start_time, end_time, instructor)
        if not working_time[0]:
            context.update({'errors': working_time[1]})
            return render(request, 'InstructorDashboard/instructor_profile.html', context)
        if not (start_time < end_time):
            context.update({"errors": "End Time can't be less then Start Time."})
            return render(request, 'InstructorDashboard/instructor_profile.html', context)
        request.user.first_name = ser.initial_data.get('first_name')
        request.user.last_name = ser.initial_data.get('last_name')
        request.user.mobile_no = ser.initial_data.get('mobile_no')
        request.user.email = ser.initial_data.get('email')
        request.user.address = ser.initial_data.get('address')
        request.user.latitude = ser.initial_data.get('latitude')
        request.user.longitude = ser.initial_data.get('longitude')
        request.user.save()
        profile_obj, created = user_models.Profile.objects.get_or_create(user=request.user)

        profile_obj.monday = bool(request.POST.get('monday') == 'on')
        profile_obj.tuesday = bool(request.POST.get('tuesday') == 'on')
        profile_obj.wednesday = bool(request.POST.get('wednesday') == 'on')
        profile_obj.thursday = bool(request.POST.get('thursday') == 'on')
        profile_obj.friday = bool(request.POST.get('friday') == 'on')
        profile_obj.saturday = bool(request.POST.get('saturday') == 'on')
        profile_obj.sunday = bool(request.POST.get('sunday') == 'on')

        profile_obj.location = ser.initial_data.get('location')
        profile_obj.about = ser.initial_data.get('about')
        profile_obj.language = ser.initial_data.get('language')
        profile_obj.facebook_link = ser.initial_data.get('facebook_link')
        profile_obj.instagram_link = ser.initial_data.get('instagram_link')
        profile_obj.twitter_link = ser.initial_data.get('twitter_link')
        profile_obj.day_start_time = request.POST.get('day_start_time')
        profile_obj.day_end_time = request.POST.get('day_end_time')

        profile_obj.save()
        profile_obj = user_models.Profile.objects.get(user=request.user)
        user_obj, created = user_models.WeekTimeSlots.objects.get_or_create(instructor_id=profile_obj.id)
        # user_obj = user_models.WeekTimeSlots.objects.all()
        # print(user_obj[1].instructor_id)
        if profile_obj.monday == True:
            user_obj.monday_startTime_slot = start_time
            user_obj.monday_endTime_slot = end_time
        if profile_obj.tuesday == True:
            user_obj.tuesday_startTime_slot = start_time
            user_obj.tuesday_endTime_slot = end_time
        if profile_obj.wednesday == True:
            user_obj.wednesday_startTime_slot = start_time
            user_obj.wednesday_endTime_slot = end_time
        if profile_obj.thursday == True:
            user_obj.thursday_startTime_slot = start_time
            user_obj.thursday_endTime_slot = end_time
        if profile_obj.friday == True:
            user_obj.friday_startTime_slot = start_time
            user_obj.friday_endTime_slot = end_time
        if profile_obj.saturday == True:
            user_obj.saturday_startTime_slot = start_time
            user_obj.saturday_endTime_slot = end_time
        if profile_obj.sunday == True:
            user_obj.sunday_startTime_slot = start_time
            user_obj.sunday_endTime_slot = end_time
        # profile_user = user_models.User.objects.get(id=request.user.id)
        # profile_user
        user_obj.save()
        stripe_msg = Strip_Message(request)
        context.update({'user_update': 'Updated Successfully ! ', 'stripe_msg': stripe_msg})
        return render(request, 'InstructorDashboard/instructor_profile.html', context)
    return render(request, 'InstructorDashboard/instructor_profile.html', context)


@login_required(redirect_field_name='login')
def profile_update(request):
    context = {}
    from .forms import ProfileImageForm
    if request.method == 'POST':
        try:
            instance = user_models.User.objects.get(id=request.user.id)
        except user_models.User.DoesNotExist:
            return redirect('InstructorDashboard:page404')

        form = ProfileImageForm(request.POST, request.FILES)
        if form.is_valid():
            instance.profile_img = form.cleaned_data['profile_img']
            instance.save()
            return redirect('InstructorDashboard:instructor_profile')
        else:
            context.update({'error': form.errors})
            return redirect('InstructorDashboard:instructor_profile')
    return redirect('InstructorDashboard:instructor_profile')


@login_required(redirect_field_name='login')
def change_password(request):
    context = {}
    if request.method == 'POST':
        ser = seializer.PasswordChange(data=request.POST)
        if ser.is_valid():
            if not (ser.data['new_password'] == ser.data['confirm_password']):
                context.update({'password_error': 'New Password and Confirm Password must be matched !'})
                return render(request, 'InstructorDashboard/instructor_profile.html', context)
            try:
                user_obj = user_models.User.objects.get(id=request.user.id)
                first_name = user_obj.first_name
                last_name = user_obj.last_name
            except user_models.User.DoesNotExist:
                return redirect('InstructorDashboard:page404')
            user_obj.set_password(str(ser.data['new_password']))
            user_obj.save()

            user_name = user_obj.get_full_name()
            user_email = request.user.email
            subject = "Password Changed - Swim Time Solutions"
            email_body = f"Hello {user_name},\n\nThis is to notify that the password of your account  on Swim Time Solutions has been changed successfully.\n\n" \
                         f"Thank You,\n" \
                         f"Swim Time Solutions"
            try:
                sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                                   'user_email': user_email})
            except Exception as e:
                pass
            context.update({'success': "Password update Successfully. Please login !! "})
            # user = authenticate(username=user_obj.username, password=user_obj.password)
            # if user:
            #     login(request, user)
            #     context.update({'password_updated': 'Password update Successfully !'})
            #     return render(request, 'InstructorDashboard/instructor_profile.html', context)
            # else:
            #     context.update({'error': "Can't login !!!"})
            return render(request, 'InstructorDashboard/auth/login.html', context)
        else:
            context.update({'errors': utility.serializer_error_to_dict(ser.errors)})
            return render(request, 'InstructorDashboard/instructor_profile.html', context)
    return render(request, 'InstructorDashboard/instructor_profile.html', context)


@login_required(redirect_field_name='login')
def class_create_view(request):
    context = {}
    if request.method == 'POST':
        ser = serializer.ClassCreateSerializer(data=request.POST, context={'user': request.user})
        if ser.is_valid():
            ser.validated_data['thumbnail_image'] = request.FILES.get('thumbnail_image')
            ser.save()
            return redirect('InstructorDashboard:class_list')
        else:
            context.update({'errors': utility.serializer_error_to_dict(ser.errors)})
            return render(request, 'InstructorDashboard/class-create-form.html', context=context)
    return render(request, 'InstructorDashboard/class-create-form.html')


@login_required(redirect_field_name='login')
def class_update_view(request, id):
    context = {}
    try:
        instance = ClassInstructor.objects.get(id=id, instructor=request.user)
    except ClassInstructor.DoesNotExist:
        return redirect('InstructorDashboard:page404')

    if request.method == 'POST':
        instance.thumbnail_image = request.FILES.get('thumbnail_image') if request.FILES.get(
            'thumbnail_image') else instance.thumbnail_image
        instance.title = request.POST.get('title')
        instance.time_slot = request.POST.get('time_slot')
        instance.total_days = request.POST.get('total_days')
        instance.description = request.POST.get('description')
        instance.price = request.POST.get('price')
        instance.save()
        return redirect("InstructorDashboard:class_list")
    return render(request, 'InstructorDashboard/class-update-form.html', {'instance': instance})


class ClassDetailView(DetailView):
    queryset = ClassInstructor.objects.all()
    template_name = 'InstructorDashboard/class-detail-view.html'
    context_object_name = 'class_obj'

    def get_success_url(self):
        return reverse('InstructorDashboard:class-list')


@login_required(redirect_field_name='login')
def class_list(request):
    classes = ClassInstructor.objects.filter(instructor=request.user).order_by('-id')
    # stripe_msg = Strip_Message(request)
    context = {'classes': classes}
    return render(request, 'InstructorDashboard/class-detail-view.html', context=context)


@login_required(redirect_field_name='login')
def class_delete(request, id):
    instance = ClassInstructor.objects.get(pk=id)
    instance.delete()
    return redirect('InstructorDashboard:class_list')


@login_required(redirect_field_name='login')
def students(request):
    ages = {}
    students = []

    bookings = appointment_model.Booking.objects.filter(class_instructor__instructor=request.user)
    for booking in bookings:
        if not (booking.user in students):
            # students.append(booking.user)
            students.append(booking.kids)
            today = date.today()
            age = today.year - booking.kids.date_of_birth.year - (
                    (today.month, today.day) < (booking.kids.date_of_birth.month, booking.kids.date_of_birth.day))
            ages[booking.kids.parent.mobile_no] = age
    # stripe_msg = Strip_Message(request)
    context = {
        'students': set(students),
        "ages": ages
    }

    return render(request, 'InstructorDashboard/students.html', context)


# **************Class Management End********************

def logout_view(request):
    logout(request)
    return redirect('InstructorDashboard:login')


def Page404(request):
    return render(request, 'InstructorDashboard/auth/page-404.html')


@login_required(redirect_field_name='login')
def booking_view(request, booking_id=None):
    if booking_id:
        pass
    else:
        bookings = appointment_model.Booking.objects.filter(class_instructor__instructor=request.user).order_by(
            "-booked_at")
        context = {'bookings': bookings}

        return render(request, 'InstructorDashboard/bookings.html', context=context)


@login_required(redirect_field_name='login')
def appointment_view(request, booking_id=None):
    if booking_id:
        pass
    else:
        print(request.user)
        appointments = appointment_model.Appointment.objects.filter(booking__class_instructor__instructor=request.user)
        # ,start_time__gt=timezone.now())
        # stripe_msg = Strip_Message(request)
        context = {'appointments': appointments.order_by('start_time')}
        return render(request, 'InstructorDashboard/appointment_view.html', context=context)


def generate_otp(request):
    if request.method == 'POST':
        context = {}
        email = request.POST.get('email')
        try:
            user = user_models.User.objects.get(email=email)
            new_otp = randint(100000, 999999)
            expiry_time = datetime.now() + timedelta(minutes=2)
            user_models.OTP.objects.filter(user=user).delete()
            otp = user_models.OTP.objects.create(otp=new_otp, user=user, otp_expired=expiry_time)

            current_site = get_current_site(request=request).domain
            email_body = f'Hello {user.first_name},' \
                         f'\nPlease use below OTP & link to reset your password\n' \
                         f'OTP: {otp.otp}' \
                         f'Link: {current_site}/user/reset-password \n\n' \
                         f"Thank You,\nTeam Swim Time Solutions"
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Reset your password - Swim Time Solutions'}
            try:
                sent_mail(data)
                context.update({'success': 'OTP has been send to your registered email address.',
                                'note': 'OTP will expire within 2 min.'})
                return render(request, 'InstructorDashboard/auth/generate_otp.html', context)
            except Exception as e:
                otp.delete()
                context.update({'error': 'Email service not working, please try after some time.'})
                return render(request, 'InstructorDashboard/auth/generate_otp.html', context)
        except user_models.User.DoesNotExist:
            context.update({'error': 'Invalid email.'})
            return render(request, 'InstructorDashboard/auth/generate_otp.html', context)

    return render(request, 'InstructorDashboard/auth/generate_otp.html')


def terms_conditions(request):
    return render(request, 'InstructorDashboard/terms_conditions.html')


# def add_break_time(request):
#     if request.method == "POST":
#         formset = BreakTimeFormSet(data=request.POST, initial=[{'instructor': request.user}])
#
#         if formset.is_valid():
#             formset.save()
#             return redirect('InstructorDashboard:instructor_profile')
#     return redirect('InstructorDashboard:instructor_profile')

def add_break_time(request):
    if request.method == "POST":
        formset = BreakTimeFormSet(data=request.POST, initial=[{'instructor': request.user}])
        break_time = user_models.Profile.objects.get(user=request.user.id)

        if request.POST['form-0-start_time'] > request.POST['form-0-end_time']:
            messages.error(request, "Please select valid timeSlot!")
            return redirect('InstructorDashboard:instructor_profile')
        elif (break_time.day_start_time).strftime("%H:%M:%S") < request.POST['form-0-start_time'] < (
                break_time.day_end_time).strftime("%H:%M:%S") and (break_time.day_start_time).strftime("%H:%M:%S") < \
                request.POST['form-0-end_time'] < (break_time.day_end_time).strftime("%H:%M:%S"):
            if formset.is_valid():
                formset.save()
                return redirect('InstructorDashboard:instructor_profile')
        else:
            messages.error(request, "Please select valid timeSlot!")

    return redirect('InstructorDashboard:instructor_profile')


def del_break_time(request, id):
    try:
        user_models.BreakTime.objects.get(id=id).delete()
    except user_models.BreakTime.DoesNotExist:
        pass
    return redirect('InstructorDashboard:instructor_profile')


def Strip_Message(request):
    instructor_email = request.session['instructor_email']
    data = StripeAccount.objects.filter(Instructor__email=instructor_email)
    if data:
        return True
    else:
        return False


def generate_otp(request):
    if request.method == 'POST':
        context = {}
        email = request.POST.get('email')
        try:
            user = user_models.User.objects.get(email=email)
            if user.user_type == 1:
                new_otp = randint(100000, 999999)
                expiry_time = datetime.now() + timedelta(minutes=2)
                user_models.OTP.objects.filter(user=user).delete()
                otp = user_models.OTP.objects.create(otp=new_otp, user=user, otp_expired=expiry_time)

                current_site = get_current_site(request=request).domain
                email_body = f"Hello {user.first_name},\n\n" \
                             f"\n\nPlease use below OTP & link to reset your password\n" \
                             f"OTP: {otp.otp}\n" \
                             f"Link: {current_site}/user/reset-password\n\n" \
                    # f" Thank You,\nTeam Swim Time Solutions"
                data = {'email_body': email_body, 'to_email': user.email,
                        'email_subject': 'Reset your password - Swim Time Solutions'}
                try:
                    sent_mail(data)
                    context.update({'success': 'OTP has been sent to your registered email address.',
                                    'note': 'OTP will expire within 2 min.'})
                    return render(request, 'InstructorDashboard/auth/generate_otp.html', context)
                except Exception as e:
                    otp.delete()
                    context.update({'error': 'Email service not working, please try after some time.'})
                    return render(request, 'InstructorDashboard/auth/generate_otp.html', context)
            else:
                context.update({'error': 'Invalid email.'})
                return render(request, 'InstructorDashboard/auth/generate_otp.html', context)
        except user_models.User.DoesNotExist:
            context.update({'error': 'Invalid email.'})
            return render(request, 'InstructorDashboard/auth/generate_otp.html', context)

    return render(request, 'InstructorDashboard/auth/generate_otp.html')


def user_pass(request):
    if request.method == 'POST':
        context = {}
        email = request.POST.get('email')

        try:
            user = user_models.User.objects.get(email=email)
            if user.user_type == 2:
                new_otp = randint(100000, 999999)
                expiry_time = datetime.now() + timedelta(minutes=2)
                user_models.OTP.objects.filter(user=user).delete()
                otp = user_models.OTP.objects.create(otp=new_otp, user=user, otp_expired=expiry_time)

                current_site = get_current_site(request=request).domain
                email_body = f'Hello {user.first_name}, \nPlease use below OTP & link to reset your password\nOTP: {otp.otp} \
                \nLink: {current_site}/user/reset-password\n\n'
                f"Thank You,\nTeam Swim Time Solutions"
                data = {'email_body': email_body, 'to_email': user.email,
                        'email_subject': 'Reset your password'}
                try:
                    sent_mail(data)
                    # context.update({'success': 'OTP has been send to your registered email address.',
                    #                 'note': 'OTP will expire within 2 min.'})
                    messages.error(request, "OTP has been sent to your registered email address.")
                    return redirect('/')
                except Exception as e:
                    otp.delete()
                    # context.update({'error': 'Email service not working, please try after some time.'})
                    # return render(request, 'register.html', context)
                    messages.error(request, "Email service not working, please try after some time.")
                    return redirect('/')
            else:
                messages.error(request, "Invalid email.")
                return redirect('/')
        except user_models.User.DoesNotExist:
            # context.update({'error': 'Invalid email.'})
            # return render(request, 'register.html', context)
            messages.error(request, "Invalid email.")
            return redirect('/')

    return redirect('/')
