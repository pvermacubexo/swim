from django.shortcuts import render
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status

from user.email_services import sent_mail
from .serializers import ContactUsSerializer
from .models import ContactUs
from django.conf import settings


class ContactUsViewSet(APIView):
    serializer_class = ContactUsSerializer()
    queryset = ContactUs.objects.all()
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        ser = ContactUsSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email_body = f"Hi , {ser.validated_data['full_name']} want's to connect to you. \n Here is the details: " \
                     f"Phone Number: {ser.validated_data['phone']} and Message: {ser.validated_data['message']}"
        try:
            data = {'email_body': email_body, 'to_email': 'paragmodi@cubexo.io',
                    'email_subject': ser.validated_data['subject']}

            sent_mail(data)
            ser.save()
            messages.success(request,"message send successfully")
            return render(request,"new_register.html")
        except Exception as e:
            messages.error(request, "something went wrong")
            return render(request, "new_register.html")
