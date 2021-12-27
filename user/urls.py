from django.conf.urls import url, include
from django.urls import path
from rest_framework import routers

from . import views

app_name = 'UserApp'
# router = routers.DefaultRouter()
router = routers.SimpleRouter(trailing_slash=False)
router.register(r'', views.UserViewSet, basename='user')
router.register(r'/profile', views.ProfileViewSet, basename='profile')
router.register(r'/student_profile', views.StudentProfileViewSet, basename='student_profile')
router.register(r'/review', views.RateReviewViewSet)
router.register(r'/generate-otp', views.OTPViewSet, basename='otp')
router.register(r'/student_update', views.StudentUpdateProfileViewset, basename='student_update')
urlpatterns = [
    path('/login', views.Authenticate.as_view(), name="api_auth"),
    path('/instructors', views.GetInstructorProfile.as_view(), name="profile"),
    path('/booked_class', views.GetBookedViewSet.as_view(), name="booked_class"),
    path('/profile_student', views.GetStudentProfileViewSet.as_view(), name="profile_student"),
    path('/request-reset-email', views.RequestPasswordResetEmail.as_view(), name="request-reset-email"),
    path('/password-reset/<uidb64>/<token>', views.PasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path('/password-reset-complete', views.SetNewPasswordAPIView.as_view(), name='password-reset-complete'),
    path('/reset-password', views.forgot_password, name='reset_password'),
    path('/instructor-slug', views.InstructorSlug.as_view()),
    path('/get-slug', views.InstructorGetSlug.as_view()),
    path('/profile_update', views.StudentProfileUpdateViewset.as_view(), name="update-user"),
    path('', include(router.urls))
]
urlpatterns += router.urls
