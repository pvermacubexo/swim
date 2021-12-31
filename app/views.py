from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect

# Create your views here.
from Appointment.models import ClassInstructor
from user import models as user_models
from user.models import User


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


def SwimTimeDashboard(request, ):
    if 'email' in request.session:
        obj = User.objects.get(email=request.session['email'])
        user_id = obj.inst_id
        first_name = User.objects.get(id=user_id)
        email = request.session['email']
        # user_details = User.objects.filter(email=email)
        user_details = User.objects.get(email=email)
        try:
            classes = ClassInstructor.objects.filter(instructor_id=user_id)

            return render(request, 'dashboard.html',
                          {"user_details": user_details, "data": classes, "first_name": first_name})
        except:
            messages.error(request,"Invalid login details")
            return render(request, "register.html")
    else:
        return render(request, "register.html")


def update_profile(request):
    if request.method == "POST":
        email = request.session['email']
        obj = User.objects.get(email=email)
        obj.first_name = request.POST['first_name']
        obj.last_name = request.POST['last_name']
        obj.address = request.POST['address']
        obj.mobile_no = request.POST['mobile_no']
        obj.DateOfBirth = request.POST['DateOfBirth']
        obj.mother_name = request.POST['mother_name']
        obj.father_name = request.POST['father_name']
        obj.profile_img = request.FILES['profile_img']
        obj.save()

        obj = User.objects.get(email=request.session['email'])
        user_id = obj.inst_id
        first_name = User.objects.get(id=user_id)
        user_details = User.objects.filter(email=email)
        classes = ClassInstructor.objects.filter(instructor_id=user_id)
        messages.success(request,"updated successfully")
        return redirect(SwimTimeDashboard)
        # return render(request, 'dashboard.html',
        #               {"user_details": user_details, "data": classes, "first_name": first_name})
    else:
        obj = User.objects.get(email=request.session['email'])
        user_id = obj.inst_id
        first_name = User.objects.get(id=user_id)
        user_details = User.objects.filter(email=request.session['email'])
        classes = ClassInstructor.objects.filter(instructor_id=user_id)
        messages.error(request,"somthing went wrong")

        return render(request, 'dashboard.html',
                      {"user_details": user_details, "data": classes, "first_name": first_name})


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
                print("hi")
                print(slug_id)
                first_name = request.POST['first_name']
                last_name = request.POST['last_name']
                email = request.POST['email']
                password = make_password(request.POST['password'])
                mobile_no = request.POST['mobile_no']
                DateOfBirth = request.POST['DateOfBirth']
                father_name = request.POST['father_name']
                mother_name = request.POST['mother_name']
                address = request.POST['address']
                # instructor_id = slug_id

                obj = User(first_name=first_name, last_name=last_name, email=email, password=password, mobile_no=mobile_no,
                           DateOfBirth=DateOfBirth, father_name=father_name, mother_name=mother_name, address=address,
                           inst_id=slug_id)
                obj.save()

                request.session['slug_id'] = slug_id
                request.session['email'] = email
                return redirect(SwimTimeDashboard)
        except:
            messages.error(request,"Already Registered user")
            return render(request, "register.html", {"id": id})
        return render(request, "register.html", {"id": id})


def LogoutView(request):
    logout(request)
    messages.success(request,"Logout Successfully")
    return render(request, "new_register.html")

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
