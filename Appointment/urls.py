from rest_framework import routers
from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf.urls.static import static
from django.conf import settings

from Appointment import views

router = routers.SimpleRouter(trailing_slash=False)
router.register(r'appointment', views.AppointmentViewSet, basename='appoinment')
router.register(r'classInstructor', views.ClassInstructorViewSet, basename='classInstructor')
# router.register(r'appointment-schedule', views.AppointmentScheduleViewSet,basename='appointment-schedule')
urlpatterns = [
    path('', include('InstructorDashboard.urls')),
    path('schedule', views.AppointmentScheduleViewSet.as_view(),name='schedule'),

    path('classes', views.InstructorClassGetViewSet.as_view()),
    path('booking-confirmation', views.ClassGetViewSet.as_view()),
    path('check-availablity', views.CheckAvailability.as_view()),
    path('book', views.BookInstructor.as_view()),
    path('availabilityslots', views.AvailabilitySlots.as_view()),
    path('timeslots', views.GetDateTimeSlots.as_view()),
    path('individual-slot', views.GetIndividualTimeSlots.as_view()),
    path('booking', views.BookClassInstructor.as_view(),name="booking"),
    path('instructor-available', views.CheckInstructorViewSet.as_view()),
    path('individual-booking', views.IndividualBookingViewSet.as_view()),
    path('appointment-schedule', views.AppointmentScheduleViewSet.as_view()),
    path('booking-delete', views.BookingDelete.as_view()),
]
urlpatterns += format_suffix_patterns(router.urls)
urlpatterns += static('/media', document_root=settings.MEDIA_ROOT)