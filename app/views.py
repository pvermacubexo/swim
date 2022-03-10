import datetime
from datetime import timedelta
from django.core.mail import send_mail
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from rest_framework import status
# Create your views here.
from Appointment.models import ClassInstructor
from user import models as user_models
from user.models import User, Profile, Kids
from StripePayment.serializers import RepaymentBookingSeralizer
from Appointment import models as appointment_model
from Appointment.models import Booking
from SharkDeck import settings
from app.email_notification import mail_notification
from SharkDeck.tasks import sent_mail_task

BASE_URL = settings.BASE_URL


def SwimTimeView(request):
    return render(request, 'index.html')


def register(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = make_password(request.POST['password'])
        mobile_no = request.POST['mobile_no']
        DateOfBirth = request.POST['DateOfBirth']
        father_name = request.POST['father_name']
        mother_name = request.POST['mother_name']
        address = request.POST['address']

        slug = id

        obj = User(first_name=first_name, last_name=last_name, email=email, password=password, mobile_no=mobile_no,
                   DateOfBirth=DateOfBirth, father_name=father_name, mother_name=mother_name, address=address)
        request.session['email'] = email
        obj.save()

        user_id = request.session['slug_id']
        first_name = User.objects.get(id=user_id)
        user_details = User.objects.filter(email=email)
        classes = ClassInstructor.objects.filter(instructor_id=user_id)
        return redirect(SwimTimeDashboard)
    else:
        return render(request, "new_register.html")
        # return render(request, 'dashboard.html',{"user_details":user_details,"data":classes,"first_name":first_name})


def SwimTimeDashboard(request):
    if 'email' in request.session:
        obj = User.objects.get(email=request.session['email'])
        user_id = obj.inst_id
        first_name = User.objects.get(id=user_id)
        email = request.session['email']
        profile_detail = Profile.objects.filter(user_id=user_id)
        # user_details = User.objects.filter(email=email)
        user_details = User.objects.get(email=email)
        kid_detail = Kids.objects.filter(parent_id=user_details.id)
        active_kid = Kids.objects.filter(parent_id=user_details.id, status=True)
        payment_range = Profile.objects.get(user_id=user_id)

        try:
            classes = ClassInstructor.objects.filter(instructor_id=user_id)

            return render(request, 'dashboard.html',

                          {"user_details": user_details, "data": classes, "first_name": first_name,
                           "profile_detail": profile_detail, "BASE_URL": BASE_URL, "kid_detail": kid_detail,
                           "active_kid": active_kid, "first_payment": payment_range})

        except:
            messages.error(request, "Invalid Login Details!")
            return render(request, "register.html")
    else:
        return render(request, "index.html")


def update_profile(request):
    try:
        if request.method == "POST":
            email = request.session['email']
            obj = User.objects.get(email=email)
            obj.first_name = request.POST['first_name']
            obj.last_name = request.POST['last_name']
            obj.address = request.POST['address']
            obj.mobile_no = request.POST['mobile_no']
            # obj.DateOfBirth = request.POST['DateOfBirth']
            # obj.mother_name = request.POST['mother_name']
            obj.father_name = request.POST['father_name']
            if 'profile_img' in request.FILES:
                obj.profile_img = request.FILES['profile_img']
            else:
                pass
            obj.save()

            for (kids, dob, ids) in zip(request.POST.getlist('kids_name'), request.POST.getlist('date_of_birth'),
                                        request.POST.getlist('ID')):
                kid_obj = Kids.objects.get(id=ids)
                kid_obj.kids_name = kids
                kid_obj.date_of_birth = dob
                kid_obj.save()

            for (kids, dob) in zip(request.POST.getlist('kids_name1'), request.POST.getlist('date_of_birth1')):
                kid_obj = Kids(kids_name=kids, date_of_birth=dob, parent_id=obj.id)
                kid_obj.save()

            obj = User.objects.get(email=request.session['email'])
            user_id = obj.inst_id
            first_name = User.objects.get(id=user_id)
            user_details = User.objects.filter(email=email)
            classes = ClassInstructor.objects.filter(instructor_id=user_id)
            messages.success(request, "Updated Successfully!")
            return redirect(SwimTimeDashboard)
            # return render(request, 'dashboard.html',
            #               {"user_details": user_details, "data": classes, "first_name": first_name})
        else:
            obj = User.objects.get(email=request.session['email'])
            user_id = obj.inst_id
            first_name = User.objects.get(id=user_id)
            user_details = User.objects.filter(email=request.session['email'])
            classes = ClassInstructor.objects.filter(instructor_id=user_id)
            messages.error(request, "Somthing Went Wrong!")

            return render(request, 'dashboard.html',
                          {"user_details": user_details, "data": classes, "first_name": first_name})
    except:
        return render(request, 'dashboard.html')


# @login_required
# def MySchedule(request):
#     user_id = request.session['slug_id']
#     first_name = User.objects.get(id=user_id)
#     email = request.session['email']
#     user_details = User.objects.filter(email=email)
#     return render(request, 'my_shedule.html',{"user_details":user_details,"first_name":first_name})

#
# def Payment(request):
#     user_id = request.session['slug_id']
#     first_name = User.objects.get(id=user_id)
#     email = request.session['email']
#     user_details = User.objects.filter(email=email)
#     return render(request, 'payment.html',{"user_details":user_details,"first_name":first_name})


def Registration(request, id):
    if 'email' in request.session:
        # return render(request, 'register.html')
        return redirect(SwimTimeDashboard)
    else:
        try:
            if request.method == "POST":
                slug = user_models.Profile.objects.get(slug=id)
                slug_id = slug.user_id
                print(request.POST)

                first_name = request.POST['first_name']
                last_name = request.POST['last_name']
                email = request.POST['email']
                password = make_password(request.POST['password'])
                mobile_no = request.POST['mobile_no']
                father_name = request.POST['father_name']
                # mother_name = request.POST['mother_name']
                address = request.POST['address']
                kids_name = request.POST['kids_name']
                date_of_birth = request.POST['date_of_birth']
                # instructor_id = slug_id

                obj = User(first_name=first_name, last_name=last_name, email=email, password=password,
                           mobile_no=mobile_no,
                           father_name=father_name, address=address, inst_id=slug_id)
                obj.save()
                kid_obj = Kids(kids_name=kids_name, date_of_birth=date_of_birth, parent_id=obj.id)
                kid_obj.save()
                request.session['slug_id'] = slug_id
                request.session['email'] = email

                user_name = obj.get_full_name()
                user_email = request.POST['email']
                subject = "Registration Successful - Swim Time Solutions"
                email_body = f"Hello {user_name},\n \nWelcome to Swim Time Solutions, " \
                             f"Your account is now set up and ready to use. Let's get started !\n\n" \
                             f"Thank You," \
                             f"\nSwim Time Solutions"

                try:
                    sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                                       'user_email': user_email})
                except Exception as e:
                    pass
                return redirect(SwimTimeDashboard)
        except:
            messages.error(request, "Already Registered User!")
            return render(request, "register.html", {"id": id})
        return render(request, "register.html", {"id": id})


def LogoutView(request):
    logout(request)
    messages.success(request, "Logout Successfully!")
    return redirect('/')


# def UserRegistrations(request):
#     user_password = make_password(request.POST['password'])
#     if request.method == 'POST':
#         user = User()
#         user.first_name = request.POST['first_name']
#         user.last_name = request.POST['last_name']
#         user.email = request.POST['email']
#         user.password = user_password
#         user.mobile_no = request.POST['mobile_no']
#         user.date_of_birth = request.POST['date_of_birth']
#         user.address = request.POST['address']
#         user.save()
#         return HttpResponseRedirect('/')
#
#
# def UserLogin(request):
#     # if request.method == 'POST':
#     #     email = request.POST['email']
#     #     password = request.POST['password']
#
#         email = request.POST['email']
#         password = request.POST['password']
#
#         user = authenticate(email=email, password=password)
#         if user is not None:
#             return redirect('/dashboard')
#         else:
#             return HttpResponse("Somthing went wrong")
#

class DeleteBooking(APIView):
    def post(self, request):
        # current_date = datetime.datetime.now() - timedelta(minutes=30)
        # current_date = current_date.replace(tzinfo=datetime.timezone.utc)
        # current_date = current_date.isoformat()
        # todays_date = str(current_date).replace('+00:00', 'Z')
        # # print("aj ki tarik",todays_date)
        booking_data = appointment_model.Booking.objects.all()
        ser = RepaymentBookingSeralizer(booking_data, many=True)
        list(ser.data)
        for i in list(ser.data):
            i = dict(i)
            if i["paid_amount"] == 0 and i["pending_amount"] == 0:
                # booking_date = i["booked_at"]
                # # print("Success")
                # if todays_date >= booking_date:
                #     # print(i["id"])
                Booking.objects.get(id=i["id"]).delete()
        # return Response({'message': 'Success'}, status=status.HTTP_200_OK)
        return Response(ser.data, status=status.HTTP_200_OK)


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def kid_delete(request, id):
    Kids.objects.get(id=id).delete()
    return Response(status=status.HTTP_200_OK)


def change_kid_status(request, id):
    """ change kid status active or inactive."""
    kid = Kids.objects.get(id=id)
    if kid.status:
        kid.status = False
        kid.save()
        return Response(status=status.HTTP_200_OK)
    else:
        kid.status = True
        kid.save()
        return Response(status=status.HTTP_200_OK)
