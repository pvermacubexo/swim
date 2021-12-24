from django.conf.urls.static import static
from django.urls import path

from SharkDeck import settings
from app import views

urlpatterns = [
    # path('', views.SwimTimeView),
    path('dashboard/', views.SwimTimeDashboard, name='dashboard_view'),
    path('dashboard/myschedule/', views.MySchedule ,name='schedule'),
    path('dashboard/re-payment/', views.Payment,name='payment'),
    path('registration/<str:id>', views.Registration,name='registration'),

    path('logout', views.LogoutView, name="LogoutView"),

    # path('register',views.Registration_view,name='registration_view'),


    # path('register', views.UserRegistrations, name="UserRegistrations"),
    # path('login', views.UserLogin, name="login"),
]

