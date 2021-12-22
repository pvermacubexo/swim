from django.contrib.auth import authenticate
from rest_framework import serializers
from datetime import datetime
from Appointment import models as appointment_model
from Appointment import views as appointment_view
from user import models as user_model
from user import validators

import re
RegexValue = '[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]'


class LoginDataVerifier(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=20)

    def get_user(self):
        return authenticate(username=self.validated_data['email'], password=self.validated_data['password'])

    def validate_email(self, email):
        return email


class AppointmentUpdate(serializers.Serializer):
    id = serializers.CharField(max_length=10)
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    remark = serializers.CharField(max_length=300, required=False)
    status = serializers.CharField(max_length=1, required=False)

    def validate(self, attrs):
        attrs['start_time'] = datetime.strptime(attrs['start_time'], '%m-%d-%Y %H:%M:%S')
        attrs['end_time'] = datetime.strptime(attrs['end_time'], '%m-%d-%Y %H:%M:%S')
        week_available = appointment_view.week_available(self.context['user'].id)
        if not (attrs['start_time'].date().strftime('%A').lower() in week_available):
            raise serializers.ValidationError({"error": f"You are in Holiday on {attrs['start_time'].date().strftime('%A').lower()}."})
        appointments = appointment_model.Appointment.objects.filter(
            booking__class_instructor__instructor=self.context['user']).exclude(id=self.context['id'])
        try:
            profile = user_model.Profile.objects.get(user__id=self.context['user'].id)
        except user_model.Profile.DoesNotExist:
            raise serializers.ValidationError({'error': f"Invalid Profile."})
        if profile.day_start_time > attrs['start_time'].time() < profile.day_end_time:
            raise serializers.ValidationError(
                {"error": f"Your Working Hour is {profile.day_start_time} to {profile.day_end_time}"})
        for appointment in appointments:
            start_datetime = appointment.start_time.strftime("%m-%d-%Y %H:%M:%S")
            end_datetime = appointment.end_time.strftime("%m-%d-%Y %H:%M:%S")
            start_datetime = datetime.strptime(start_datetime, '%m-%d-%Y %H:%M:%S')
            end_datetime = datetime.strptime(end_datetime, '%m-%d-%Y %H:%M:%S')
            if start_datetime <= attrs['start_time'] <= end_datetime:
                raise serializers.ValidationError(
                    {"error": f"You already have an Appointment on {attrs['start_time']}"})
        return attrs


class PasswordChange(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if not attrs['new_password'] == attrs['confirm_password']:
            raise serializers.ValidationError({'password_error': 'Password must be same '})
        elif int(len(attrs['new_password'])) < 7 or int(len(attrs['confirm_password'])) < 7:
            raise serializers.ValidationError({'password_error': "Password must contain at-least  8 character "})
        elif not re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', attrs['new_password']):
            raise serializers.ValidationError(
                {'password_error': f"Password must contain at least 1 symbol: A-Z a-z 0-9 @#$%^&*_"}
            )
        return attrs
