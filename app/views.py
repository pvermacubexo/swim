from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from user import models as user_models

# Create your views here.
from Appointment.models import ClassInstructor, Appointment
from user.models import Profile, User


def SwimTimeView(request):
    return render(request, 'index.html')


def SwimTimeDashboard(request):
    user_id = request.session['slug_id']
    classes = ClassInstructor.objects.filter(instructor_id=user_id)
    return render(request, 'dashboard.html',{"data":classes})


# @login_required
def MySchedule(request):

    return render(request, 'my_shedule.html')


def Payment(request):

    return render(request, 'payment.html')


def Registration(request, id):
    slug = user_models.Profile.objects.get(slug=id)
    slug_id = slug.user_id
    print(slug_id)
    request.session['slug_id'] = slug_id




    return render(request, 'register.html')


def LogoutView(request):
    logout(request)
    return render(request, "index.html")

#
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
