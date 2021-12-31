import logging
from datetime import datetime, timedelta
from random import randint

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.encoding import smart_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status, generics
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from Appointment.models import Appointment, ClassInstructor, Booking
from SharkDeck.constants import user_constants
from app.views import SwimTimeDashboard
from .decorators import authorize
from .email_services import sent_mail
from .models import User, ReviewRate, get_active_users, Profile, OTP, StudentProfile
from .serializer import UserSerializer, AuthenticationSerializer, RateReviewSerializer, \
    ProfileSerializer, ResetPasswordEmailRequestSerializer, SetNewPasswordSerializer, GetBookedClass, \
    UserUpdateSerializer, UserDeletedSerializer, InstructorProfileSerializer, StudentSerializer, \
    OTPSerializer, InstructorSlugSerializer, StudentProfileSerializer, studentUsererializer, StudentUpdateSerializer, \
    StudentProfileUpdateSerializer

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Authenticate(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = AuthenticationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            email = request.POST['email']
            try:
                obj = User.objects.get(email=email)
                user_id = obj.inst_id
                classes = ClassInstructor.objects.filter(instructor_id=user_id)
                email = serializer.data.get('email')
                request.session['email'] = email
                user_details = User.objects.filter(email=email)
                if user_details:
                    messages.success(request,"User login successfully")
                    return redirect(SwimTimeDashboard)
                else:
                    messages.error(request,"Invalid login Details")
                    return render(request, "new_register.html")


            except User.DoesNotExist:
                messages.error(request,serializer.validated_data)
                return render(request, "new_register.html")
        else:
            messages.error(request, serializer.validated_data)
            return render(request, "new_register.html")





def get_deactivated_user(email, username):
    # if User.objects.filter(deactivate=False, username=username):
    #     raise AuthenticationFailed({'error': 'Username Already exist.'})
    if User.objects.filter(deactivate=False, email=email):
        raise AuthenticationFailed({'error': 'Email Already exist.'})
    if User.objects.filter(deactivate=True, email=email):
        return User.objects.filter(email=email).first()
    # if User.objects.filter(deactivate=True, username=username):
    #     return User.objects.filter(username=username).first()


class UserViewSet(ModelViewSet):
    # permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    queryset = get_active_users()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "dashboard.html"

    @authorize(user_constants.All)
    def get_queryset(self):
        if not self.user.user_type == user_constants.Admin:
            return get_active_users().filter(email=self.user.email).exclude(password=None)
        else:
            return get_active_users().all()

    def post(self, request, *args, **kwargs):

        try:
            delete_user_instance = User.objects.filter(deactivate=True, email=request.data['email'])
            if delete_user_instance:
                deleted_serializer = UserDeletedSerializer(data=request.data, context={'user': self.request.user})
                deleted_serializer.is_valid(raise_exception=True)
                # todo : send proper response for API.
                # delete_user_instance.deactivate = False
                # delete_user_instance.password = deleted_serializer.validated_data.get('password')
                # delete_user_instance.username = deleted_serializer.validated_data.get('username')
                # # print(deleted_serializer.data)
                # deleted_serializer.save()
                if deleted_serializer.initial_data['user_type'] == user_constants.Instructor:
                    profile_id = Profile.objects.filter(email=deleted_serializer.initial_data['email'])
                    # logger.info(f'New User create successfully {deleted_serializer.data}')
                    return Response({'user': deleted_serializer.initial_data, 'profile_id': profile_id},
                                    status=status.HTTP_201_CREATED)
                return Response({'user': deleted_serializer.initial_data}, status=status.HTTP_201_CREATED)
        except:
            pass

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.user_type == user_constants.Instructor:
            profile = Profile.objects.create(user_id=user.id)
            logger.info(f'New Instructor create successfully {serializer.data}')
            return Response({'user': serializer.data, 'profile': profile.id}, status=status.HTTP_201_CREATED)
        if user.user_type == user_constants.Trainee:
            ser = StudentSerializer(data=request.data, context={'user': user})
            if ser.is_valid():
                try:
                    user_id = request.session['slug_id']
                    ser.save()
                    logger.info(f'New Student create successfully {serializer.data}')
                    return render(request, "dashboard.html", {'user': serializer.data, 'student_profile': ser.data})
                except:
                    msg = "invalid URL"
                    return render(request, "new_register.html")
            else:
                user.delete()
                return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        logger.info(f'New Super User create successfully {serializer.data}')
        # return Response({'user': serializer.data}, status=status.HTTP_201_CREATED)
        # return render(request, self.template_name,{'user': serializer.data})

        return render(request, "dashboard.html", {'data': serializer.data})

    @authorize([user_constants.Trainee, user_constants.Admin])
    def update(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data, context={'user': self.user})
        serializer.is_valid(raise_exception=True)
        serializer.update(self.user, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentUpdateProfileViewset(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @authorize([user_constants.Trainee])
    def get_queryset(self):
        try:
            user = User.objects.filter(id=self.user.id)
            return user
        except User.DoesNotExist:
            return Response({'message': 'user does not exist with this id'}, status=status.HTTP_400_BAD_REQUEST)

    @authorize([user_constants.Trainee])
    def create(self, request, *args, **kwargs):

        user = User.objects.get(id=self.user.id)
        ser = studentUsererializer(data=request.data, context={'user_pass': user.password})
        ser.is_valid(raise_exception=True)
        update_data = ser.update(self.user, ser.validated_data)
        student_profile = StudentProfile.objects.get(user=self.user)
        student_profile.father_name = ser.data['father_name']
        student_profile.mother_name = ser.data['mother_name']
        student_profile.DateOfBirth = ser.data['DateOfBirth']
        student_profile.save()
        return Response({'message': 'success'}, status=status.HTTP_200_OK)


class StudentProfileUpdateViewset(APIView):

    # @authorize([user_constants.Trainee])
    def post(self, request):
        print(self.request.data['method'])
        if (self.request.data['method'] == 'PATCH'):
            user_ser = StudentUpdateSerializer(data=request.data, context={'user': request.user})
            try:
                student_profile = StudentProfile.objects.get(user=request.user)
            except StudentProfile.DoesNotExist:
                return Response({'error': 'Invalid Student ID.'})

            user_profile_ser = StudentProfileUpdateSerializer(data=request.data, context={'user': request.user})
            user_ser.is_valid(raise_exception=True)
            user_profile_ser.is_valid(raise_exception=True)
            user_ser.update(request.user, user_ser.validated_data)
            user_profile_ser.update(student_profile, user_profile_ser.validated_data)
            return Response({'user': user_ser.data, 'student': user_profile_ser.data}, status=status.HTTP_200_OK)
        return HttpResponse({"Hello": "Bhai"})


class ProfileViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    @authorize(user_constants.All)
    def get_queryset(self):
        if self.user.user_type == user_constants.Trainee:
            cls = ClassInstructor.objects.all()
            return Profile.objects.filter(user__user_type=user_constants.Instructor,
                                          user__deactivate=False).filter(user__in=[x.instructor.id for x in cls])

        elif self.user.user_type == user_constants.Instructor:
            return Profile.objects.filter(user=self.user).order_by('-id')
        else:
            return Profile.objects.filter(user__deactivate=False).order_by('-id')

    @authorize([user_constants.Instructor])
    def update(self, request, *args, **kwargs):
        try:
            profile_instance = Profile.objects.get(user_id=self.user.id)
        except Profile.DoesNotExist:
            logger.warning(f"Instructor = {self.user} have not Profile.")
            return Response({'not_found': 'User have not profile'}, status=status.HTTP_204_NO_CONTENT)
        profile_serializer = ProfileSerializer(data=request.data, context={'user': self.user})
        user_serializer = UserUpdateSerializer(data=request.data, context={'user': self.user})
        user_serializer.is_valid(raise_exception=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.update(profile_instance, profile_serializer.validated_data)
        user_serializer.update(self.user, user_serializer.validated_data)
        return Response({'profile': profile_serializer.data, 'user': user_serializer.data})


class StudentProfileViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = StudentProfileSerializer
    queryset = StudentProfile.objects.all()

    @authorize([user_constants.Trainee])
    def get_queryset(self):
        return StudentProfile.objects.filter(user__id=self.user.id)

    @authorize([user_constants.Trainee])
    def update(self, request, *args, **kwargs):
        try:
            student_instance = StudentProfile.objects.get(user_id=self.user.id)
        except StudentProfile.DoesNotExist:
            logger.warning(f"Student with this id = {self.user} have not Profile.")
            return Response({'not_found': 'User have not profile'}, status=status.HTTP_204_NO_CONTENT)
        profile_serializer = StudentProfileSerializer(data=request.data, context={'user': self.user})
        user_serializer = studentUsererializer(data=request.data, context={'user': self.user})
        user_serializer.is_valid(raise_exception=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.update(student_instance, user_serializer.validated_data)
        user_serializer.update(self.user, user_serializer.validated_data)
        return Response({'profile': profile_serializer.data, 'user': user_serializer.data})


class GetStudentProfileViewSet(APIView):
    @authorize([user_constants.Trainee])
    def get(self, request):
        try:
            user_profile = StudentProfile.objects.get(user=self.user)
            user_profile = StudentProfileSerializer(user_profile, many=False)
            return Response(user_profile.data)
        except StudentProfile.DoesNotExist:
            return Response({'message': 'user does not exist.'}, status=status.HTTP_400_BAD_REQUEST)


class RateReviewViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = RateReviewSerializer
    queryset = ReviewRate.objects.all()

    @authorize([user_constants.Instructor, user_constants.Trainee])
    def get_queryset(self):
        return ReviewRate.objects.all()

    @authorize([user_constants.Trainee])
    def create(self, request, *args, **kwargs):
        serializer = RateReviewSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            try:
                rate_obj = ReviewRate.objects.get(rated_to=serializer.validated_data['rated_to'].id,
                                                  rated_by=self.user.id)
                if rate_obj:
                    rate_obj.rating = serializer.data['rating']
                    rate_obj.review = serializer.data['review']
                    rate_obj.save()
                    logger.info(f"{request.user} update rating")
                    return Response(serializer.data, status=status.HTTP_200_OK)
            except ReviewRate.DoesNotExist:
                if not Booking.objects.filter(user=request.user,
                                              class_instructor__instructor=serializer.validated_data['rated_to'].id):
                    logger.warning(
                        f"{request.user} don't book any class of Instructor = {serializer.validated_data['rated_to']}")
                    return Response({'error': 'User does not book any Class of this Instructor'})
                serializer.validated_data['rated_by'] = request.user
                serializer.save()
                logger.info(
                    f"{request.user}'s Rate or Review is successfully added to {serializer.validated_data['rated_to']}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetBookedViewSet(APIView):
    @authorize([user_constants.Trainee])
    def get(self, request):
        try:
            appointment = Appointment.objects.filter(booking__user=request.user).order_by('start_time')
            serializer = GetBookedClass(appointment, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response({'error': 'Please Book Any Class.'}, status=status.HTTP_404_NOT_FOUND)


class GetInstructorProfile(APIView):
    def get(self, request):
        ser = InstructorProfileSerializer(Profile.objects.all(), many=True, context={'request': self.request})
        return Response(ser.data, status=status.HTTP_200_OK)


class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        email = request.data['email']
        if get_active_users().filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request=request).domain
            relativeLink = reverse(
                'password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            absurl = 'http://' + current_site + relativeLink
            email_body = 'Hello, \n Use link below to reset your password  \n' + \
                         absurl
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Reset your password'}
            sent_mail(data)
            return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)


class PasswordTokenCheckAPI(generics.GenericAPIView):

    def get(self, request, uidb64, token):
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = get_active_users().get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'error': 'Token is not valid, please request a new one '},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'success': True,
                'message': 'credential valid',
                'uidb64': uidb64,
                'token': token
            })
        except DjangoUnicodeDecodeError as identifier:
            return Response({'error': 'Token is not valid, please request a new one '},
                            status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def put(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)


def forgot_password(request):
    if request.method == 'POST':
        context = {}
        email = request.POST.get('email')
        otp = request.POST.get('otp')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')
        if not (password == confirm_password):
            context.update({'error': 'Password must be same.'})
            return render(request, 'forgot_password.html', context)
        if len(password) < 8:
            context.update({'error': 'Password length should be at-least 8 digit.'})
            return render(request, 'forgot_password.html', context)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            context.update({'error': 'Please enter valid email address.'})
            return render(request, 'forgot_password.html', context)
        try:
            otp = OTP.objects.get(user=user, otp=otp, otp_expired__gte=datetime.now())
        except OTP.DoesNotExist:
            context.update({'error': 'Invalid email or OTP.'})
            return render(request, 'forgot_password.html', context)
        user.password = make_password(password)
        user.save()
        otp.delete()
        context.update({'success': 'Password updated successfully'})
        return render(request, 'forgot_password.html', context)

    return render(request, 'forgot_password.html')


class OTPViewSet(ModelViewSet):
    serializer_class = OTPSerializer
    permission_classes = (AllowAny,)
    queryset = OTP.objects.all()
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        data = self.request.data
        try:
            user = User.objects.get(email=data['email'])
            new_otp = randint(100000, 999999)
            expiry_time = datetime.now() + timedelta(minutes=2)
            OTP.objects.filter(user=user).delete()
            otp = OTP.objects.create(otp=new_otp, user=user, otp_expired=expiry_time)

            current_site = 'http://167.172.131.164'
            email_body = f'Hello, {user.email} OTP = {otp.otp} \
            Use link below to reset your password {current_site}/user/reset-password'
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Reset your password'}
            try:
                sent_mail(data)
                return Response({'email': user.email,
                                 'message': 'OTP has been send to your registered email address.',
                                 'note': 'OTP will expire within 2 min.'},
                                status=status.HTTP_200_OK)
            except Exception as e:
                otp.delete()
                return Response({'error': 'Email service not working, please try after some time.'},
                                status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email.'}, status=status.HTTP_400_BAD_REQUEST)


class InstructorSlug(APIView):
    def post(self, request):
        try:
            instructor_profile = Profile.objects.get(slug=request.data.get('slug'))
            ser = InstructorSlugSerializer(instructor_profile, many=False)
            return Response(ser.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'error': 'Instructor not found.'}, status=status.HTTP_404_NOT_FOUND)


class InstructorGetSlug(APIView):
    @authorize([user_constants.Trainee])
    def get(self, request):
        try:
            student = StudentProfile.objects.get(user=request.user)
        except StudentProfile.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'slug': student.get_instructor_slug}, status=status.HTTP_200_OK)
