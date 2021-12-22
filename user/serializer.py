import logging
import datetime

from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.sites.shortcuts import get_current_site

from Appointment.models import Appointment, Booking
from Appointment.serializer import ClassInstructorInfoSerializer, ClassInstructor
from .models import User, ReviewRate, Profile, StudentProfile, OTP
from SharkDeck.constants import user_constants
import math

# Get an instance of a logger
logger = logging.getLogger(__name__)


class AuthenticationSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        attrs['email'] = attrs['email'].lower()
        data = super().validate(attrs)
        try:
            student = StudentProfile.objects.filter(user__email=attrs['email']).first()
            if student.instructor:
                data['instructor_id'] = student.instructor.id
                data['instructor_slug'] = student.get_instructor_slug
            else:
                data['instructor_slug'] = None
                data['instructor_id'] = None
        except Exception:
            pass
        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['id'] = self.user.id
        data['email'] = self.user.email
        # data['username'] = self.user.username
        data['user_type'] = self.user.user_type
        # data['instructor_id'] = student.instructor.id
        logger.info(f'User login successfully with this Credentials : {data}')
        return data


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    # username = serializers.CharField(required=True)

    class Meta:
        model = User
        extra_kwargs = {'password': {'write_only': True}}
        fields = '__all__'

    def validate_email(self, obj):
        if User.objects.filter(deactivate=False, email=obj.lower()).exists():
            raise serializers.ValidationError('email already exist.')
        return obj.lower()

    # def validate_username(self, obj):
    #     if User.objects.filter(deactivate=False, username=obj).exists():
    #         raise serializers.ValidationError('username  already exist.')
    #     return obj

    def validate(self, attrs):
        attrs['is_active'] = True
        attrs['password'] = make_password(attrs['password'])
        return attrs


class StudentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(required=False)
    instructor = serializers.CharField(required=False)

    class Meta:
        model = StudentProfile
        fields = "__all__"

    def validate(self, attrs):
        if 'instructor' in attrs.keys():
            try:
                profile = Profile.objects.get(slug=attrs['instructor'])
                attrs['instructor'] = profile.user
            except Profile.DoesNotExist:
                attrs['instructor'] = None
                # raise serializers.ValidationError({'error': 'Instructor not found.'})
        else:
            attrs['instructor'] = None

        attrs['user'] = self.context['user']
        return attrs


class StudentProfileSerializer(serializers.ModelSerializer):
    user = serializers.CharField(required=False)
    instructor = serializers.CharField(required=False)

    class Meta:
        model = StudentProfile
        fields = "__all__"


class StudentGetProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class studentUsererializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    mobile_no = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    # profile_img = serializers.ImageField(required=True)
    father_name = serializers.CharField(required=True)
    mother_name = serializers.CharField(required=True)
    DateOfBirth = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = "__all__"

    def validate(self, attrs):
        attrs['is_active'] = True
        attrs['password'] = self.context['user_pass']
        return attrs


class StudentUpdateSerializer(serializers.ModelSerializer):
    mobile_no = serializers.CharField()
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'mobile_no', 'address', 'email', 'address', 'profile_img']

    def validate_mobile_no(self, attrs):
        return attrs

    def validate_email(self, obj):
        if User.objects.filter(email=obj).exclude(email=self.context['user'].email).exists():
            raise serializers.ValidationError('email already taken. please try another.')
        return obj


class StudentProfileUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudentProfile
        fields = ['father_name', 'mother_name', 'DateOfBirth']


class GetStudentProfile(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'


class GetStudentUserProfile(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class UserDeletedSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    # username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = '__all__'

    def validate(self, attrs):
        attrs['deactivate'] = False
        password = make_password(attrs['password'])
        # print(attrs)
        user = User.objects.filter(email=attrs['email']).update(deactivate=False, password=password)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    # username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = '__all__'

    def validate_email(self, obj):
        if User.objects.filter(email=obj).exclude(email=self.context['user'].email).exists():
            raise serializers.ValidationError('email already exist.')
        return obj

    # def validate_username(self, obj):
    #     if User.objects.filter(username=obj).exclude(email=self.context['user'].username).exists():
    #         raise serializers.ValidationError('username already exist.')
    #     return obj

    def validate(self, attrs):
        attrs['is_active'] = True
        attrs['password'] = make_password(attrs['password'])
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False)
    language = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    total_classes = serializers.SerializerMethodField()
    happy_students = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = '__all__'

    def get_language(self, profile):
        return profile.language.split(',') if profile.language else None

    def get_total_classes(self, obj):
        class_count = ClassInstructor.objects.filter(instructor=obj.user).count()
        return class_count if (class_count < 10) else int(math.floor(class_count / 10)) * 10

    def get_happy_students(self, obj):
        total_students = len(
            set(booking.user for booking in Booking.objects.filter(class_instructor__instructor=obj.user)))
        return total_students if (total_students < 10) else int(math.floor(total_students / 10)) * 10

    def validate(self, attrs):
        return attrs

    def get_rating(self, user):
        try:
            rating_count = 0
            total_rating = 0
            ratings = ReviewRate.objects.filter(rated_to__user_type=user_constants.Instructor)
            for rating in ratings:
                rating_count += rating.rating
            if rating_count:
                total_rating = rating_count / ratings.count()
            return total_rating
        except ReviewRate.DoesNotExist:
            return "Not Review Yet"


class InstructorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False)
    profile_img = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = '__all__'

    def get_profile_img(self, obj):
        request = self.context['request']
        path = get_current_site(request=request).domain
        return path + str(obj.user.profile_img)


class RateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewRate
        fields = '__all__'
        read_only_fields = ('rated_by',)


class GetBookedClass(serializers.ModelSerializer):
    booking = ClassInstructorInfoSerializer()
    start_time = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = '__all__'

    def get_start_time(self, obj):
        return datetime.datetime.strftime(obj.start_time, "%a, %d/%m/%y, %I:%M%p")
        # return obj.start_time


# ==================== Reset Password ==========
class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ['email']


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=8, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)

            user.set_password(password)
            user.save()

            return (user)
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)


class OTPSerializer(serializers.ModelSerializer):
    otp_expired = serializers.CharField(required=False)
    user = serializers.CharField(required=False)
    otp = serializers.CharField(required=False)
    email = serializers.CharField(required=True)

    class Meta:
        model = OTP
        fields = '__all__'


class InstructorSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
