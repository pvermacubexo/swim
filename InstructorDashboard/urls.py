"""SharkDeck URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from . import views


app_name = 'InstructorDashboard'
router = routers.SimpleRouter(trailing_slash=False)
urlpatterns = [
    path('register', views.signup_view, name='register'),
    path('login', views.login_view, name='login'),
    path('logout', views.user_logout, name='user_logout'),
    path('generate-otp', views.generate_otp, name='forgot_password'),
    path('trainee/<str:trainee>', views.trainee_view, name='trainee_view'),
    path('booking/update/<int:id>', views.update_booking, name='update_appointment'),
    path('profile', views.instructor_profile, name='instructor_profile'),
    path('change/password', views.change_password, name='change_password'),
    path('profile/', views.profile_update, name='profile_update'),
    path('bookings/', views.booking_view, name='booking_view'),
    path('appointments/', views.appointment_view, name='appointment_view'),
    path('update/transaction/<int:id>', views.update_transaction, name='update_transaction'),
    path('delete/transaction/<int:id>', views.delete_transaction, name='delete_transaction'),

    path('', views.dashboard_view, name='dashboard_view'),

    path('class/detail/<int:pk>', views.ClassDetailView.as_view(), name='class_detail_view'),
    path('class/list', views.class_list, name='class_list'),
    path('students/list', views.students, name='students'),
    path('class/create', views.class_create_view, name='class_create_form'),
    path('class/update/<int:id>', views.class_update_view, name='class_update_form'),
    # path('class-submit/', views.class_edit_view, name='class_edit_form'),
    path('class/delete/<int:id>', views.class_delete, name='class_delete'),

    path('page404', views.Page404, name='page404'),
    path('terms-contions', views.terms_conditions, name='terms_conditions'),
    path('break-time', views.add_break_time, name='add_break_time'),
    path('del-time/<int:id>', views.del_break_time, name='del_break_time'),
]
urlpatterns += format_suffix_patterns(router.urls)
# handler404 = 'InstructorDashboard.views.Page404'

