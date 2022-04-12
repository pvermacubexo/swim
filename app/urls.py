from django.conf.urls.static import static
from django.urls import path

from SharkDeck import settings
from app import views

urlpatterns = [
    # path('', views.SwimTimeView),
    path('dashboard/', views.SwimTimeDashboard, name='dashboard_view'),
    path('update-profile/', views.update_profile, name='update-profile'),
    # path('dashboard/myschedule/', views.MySchedule ,name='schedule'),
    # path('dashboard/re-payment/', views.Payment,name='payment'),
    path('instructor/<str:id>', views.Registration, name='registration'),
    path('register', views.register, name="register"),
    path('logout', views.LogoutView, name="LogoutView"),
    path('delete-booking', views.DeleteBooking.as_view()),
    path('kid_delete/<int:id>', views.kid_delete, name="kid_delete"),
    path('change_kid_status/<int:id>', views.change_kid_status, name="change_kid_status"),
    path('terms_condition/', views.TermsConditionView)

    # path('register',views.Registration_view,name='registration_view'),

    # path('register', views.UserRegistrations, name="UserRegistrations"),
    # path('login', views.UserLogin, name="login"),
]
