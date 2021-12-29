from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from rest_framework import routers
router = routers.SimpleRouter(trailing_slash=False)
router.register(r'', views.ContactUsViewSet, basename="contact_us")
urlpatterns = [

]
urlpatterns += format_suffix_patterns(router.urls)