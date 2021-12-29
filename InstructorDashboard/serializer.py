from django.contrib.auth import authenticate
from rest_framework import serializers

from Appointment.models import ClassInstructor


class LoginDataVerifier(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=20)

    def get_user(self):
        return authenticate(username=self.validated_data['email'], password=self.validated_data['password'])

    def validate_email(self, email):
        return email


# class ClassCreateSerializer(serializers.Serializer):
#     title = serializers.CharField(required=True, allow_blank=False)
#     time_slot = serializers.IntegerField(required=True)
#     total_days = serializers.IntegerField(required=True)
#     description = serializers.CharField(max_length=1000, required=True)
#     fees = serializers.IntegerField(default=0)
#     # image = serializers.ImageField(allow_empty_file=True, use_url=True)

class ClassCreateSerializer(serializers.ModelSerializer):
    instructor = serializers.CharField(required=False)

    class Meta:
        model = ClassInstructor
        fields = '__all__'

    def validate(self, attrs):
        attrs['instructor'] = self.context['user']
        return attrs


class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=20)
    last_name = serializers.CharField(max_length=20)
    email = serializers.EmailField(max_length=100)
    mobile_no = serializers.CharField(max_length=20)
    address = serializers.CharField(max_length=100, required=False)
    latitude = serializers.CharField(max_length=100, required=False)
    longitude = serializers.CharField(max_length=100, required=False)
    facebook_link = serializers.URLField(max_length=100, required=False)
    instagram_link = serializers.URLField(max_length=100, required=False)
    twitter_link = serializers.URLField(max_length=100, required=False)

    monday = serializers.CharField(max_length=6, allow_blank=True, required=False)
    tuesday = serializers.CharField(max_length=6, allow_blank=True, required=False)
    wednesday = serializers.CharField(max_length=6, allow_blank=True, required=False)
    thursday = serializers.CharField(max_length=6, allow_blank=True, required=False)
    friday = serializers.CharField(max_length=6, allow_blank=True, required=False)
    saturday = serializers.CharField(max_length=6, allow_blank=True, required=False)
    sunday = serializers.CharField(max_length=6, allow_blank=True, required=False)
