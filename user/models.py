from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.apps import apps
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models
import datetime
from django.utils.timezone import now as timezone_now
from SharkDeck.constants import user_constants
from django.shortcuts import render, redirect
from datetime import date




class CustomManager(BaseUserManager):

    def _create_user(self,  email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        # username = GlobalUserModel.normalize_username(username)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active',True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_active') is not True:
            raise ValueError('Superuser must have is_active=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    username = None
    email = models.EmailField(unique=True, max_length=100, null=False, blank=False)
    password = models.CharField(max_length=100, null=False, blank=False, validators=[
        RegexValidator(r'[A-Za-z0-9@#$%^&+=]{8,}',
                       message='The password must contain at least one in  A-Z and a-z, 0-9 and special character.')])
    mobile_no = models.CharField(unique=True, null=True, blank=True, max_length=25)
    profile_img = models.ImageField(upload_to='Images/profile', default='Images/profile/default.png', blank=True,
                                    null=False)
    deactivate = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    user_type_choices = (
        (user_constants.Instructor, "Instructor"),
        (user_constants.Trainee, "Trainee"),
        (user_constants.Admin, "Admin"),
    )
    user_type = models.IntegerField(choices=user_type_choices, default=user_constants.Trainee)
    mother_name = models.CharField(max_length=300, blank=True, null=True)
    father_name = models.CharField(max_length=200, blank=True, null=True)
    DateOfBirth = models.DateField(blank=True,null=True)
    address = models.CharField(max_length=150, null=False, blank=False)
    inst_id = models.CharField(max_length=120,blank=True)
    latitude = models.CharField(null=True, blank=True, max_length=50, validators=[
        RegexValidator(r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)$',
                       message='Not a valid latitude')])
    longitude = models.CharField(null=True, blank=True, max_length=50, validators=[
        RegexValidator(r'^\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$',
                       message='Not a valid longitude')])
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['password', 'user_type']
    objects = CustomManager()

    # def delete(self, *args, **kwargs):
    #     self.deactivate = True
    #     self.save()

    @property
    def is_instructor(self):
        return self.user_type == user_constants.Instructor

    @property
    def is_admin(self):
        return self.user_type == user_constants.Admin

    def get_full_name(self):
        return super().get_full_name() if (self.first_name and self.last_name) else self.email

    @property
    def get_profile(self):
        profile = Profile.objects.filter(user=self).first()
        return profile

    @property
    def get_monday_start_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.monday_startTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_monday_end_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.monday_endTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_tuesday_start_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.tuesday_startTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_tuesday_end_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.tuesday_endTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_wednesday_start_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.wednesday_startTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_wednesday_end_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.wednesday_endTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_thursday_start_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.thursday_startTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_thursday_end_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.thursday_endTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_friday_start_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.friday_startTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_friday_end_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.friday_endTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_saturday_start_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.saturday_startTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_saturday_end_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.saturday_endTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_sunday_start_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.sunday_startTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_sunday_end_slot(self):
        try:
            weekly_time_slot = WeekTimeSlots.objects.filter(instructor__user=self).first()
            return weekly_time_slot.sunday_endTime_slot.strftime("%H:%M:%S")
        except Exception:
            return False

    @property
    def get_day_start_time(self):
        try:
            profile = Profile.objects.filter(user=self).first()
            return profile.day_start_time.strftime("%H:%M")
        except Exception:
            return False

    @property
    def get_day_end_time(self):
        try:
            profile = Profile.objects.filter(user=self).first()
            return profile.day_end_time.strftime("%H:%M")
        except Exception:
            return False

    @property
    def get_student_profile(self):
        return StudentProfile.objects.filter(user=self).first()

    @property
    def get_age(self):
        student = StudentProfile.objects.filter(user=self).first()
        today = date.today()
        age = today.year - student.DateOfBirth.year - (
                (today.month, today.day) < (student.DateOfBirth.month, student.DateOfBirth.day))
        return age

    def get_review(self):
        return ReviewRate.objects.all()

    # def __str__(self):
    #     return self.get_full_name()


class ReviewRate(models.Model):
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = "Instructor's Review"

    rated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rated_by')
    rated_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rated_to')
    rating = models.IntegerField(null=True, blank=True)
    review = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.rated_by.email


class StudentProfile(models.Model):
    class Meta:
        verbose_name = 'Students'
        verbose_name_plural = 'Students Profile'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False, related_name='instructor')
    # parent_name = models.CharField(max_length=300, null=False, blank=False)
    father_name = models.CharField(max_length=300, null=False, blank=False)
    mother_name = models.CharField(max_length=300, null=False, blank=False)
    DateOfBirth = models.DateField(null=False, blank=False)

    @property
    def get_instructor_slug(self):
        return Profile.objects.filter(user=self.instructor).first().slug

    def __str__(self):
        return self.user.get_full_name()


class Profile(models.Model):
    class Meta:
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructor Profile'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.CharField(max_length=30, null=False, blank=False)
    url = models.CharField(max_length=150, null=False, blank=False)
    location = models.CharField(max_length=500, null=True, blank=True)
    about = models.CharField(max_length=1500, null=True, blank=True)
    language = models.CharField(max_length=500, null=True, blank=True)
    facebook_link = models.CharField(max_length=500, null=True, blank=True)
    instagram_link = models.CharField(max_length=500, null=True, blank=True)
    twitter_link = models.CharField(max_length=500, null=True, blank=True)
    day_start_time = models.TimeField(null=True, default=timezone_now)
    day_end_time = models.TimeField(null=True, default=timezone_now)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email


class OTP(models.Model):
    otp = models.IntegerField()
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='otp_created_by_user')
    otp_created = models.DateTimeField(auto_now_add=True)
    otp_expired = models.DateTimeField()


def get_active_users():
    return User.objects.filter(deactivate=False)


class WeekTimeSlots(models.Model):
    class Meta:
        verbose_name = 'Weekly break Time'
        verbose_name_plural = 'Weekly break Time'

    instructor = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        verbose_name='Instructor slots',
        help_text="Instructor required.",
        error_messages={'error': "Instructor must be required."}
    )
    monday_startTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Monday break time start',
        help_text="Choose monday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    monday_endTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Monday break time end',
        help_text="Choose monday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    tuesday_startTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Tuesday break time start',
        help_text="Choose tuesday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    tuesday_endTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Tuesday break time end',
        help_text="Choose tuesday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    wednesday_startTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Wednesday break time start',
        help_text="Choose wednesday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    wednesday_endTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Wednesday break time end',
        help_text="Choose wednesday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    thursday_startTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Thursday break time start',
        help_text="Choose thursday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    thursday_endTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Thursday break time end',
        help_text="Choose thursday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    friday_startTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Friday break time start',
        help_text="Choose friday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    friday_endTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Friday break time end',
        help_text="Choose friday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    saturday_startTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Saturday break time start',
        help_text="Choose saturday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    saturday_endTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Saturday break time end',
        help_text="Choose saturday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    sunday_startTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Sunday break time start',
        help_text="Choose sunday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )
    sunday_endTime_slot = models.TimeField(
        null=False,
        blank=False,
        default=timezone_now,
        verbose_name='Sunday break time end',
        help_text="Choose sunday start break time slot or set it current time.",
        error_messages={'error': "Choose a valid time format."}
    )

monday, tuesday, wednesday, thursday, friday, saturday, sunday = '1', '2', '3', '4', '5', '6', '7'


class BreakTime(models.Model):
    class Meta:
        verbose_name = 'Break Time'
        verbose_name_plural = 'Break Time'

    week_name = (
        (monday, 'monday'),
        (tuesday, 'tuesday'),
        (wednesday, 'wednesday'),
        (thursday, 'thursday'),
        (friday, 'friday'),
        (saturday, 'saturday'),
        (sunday, 'sunday'),
    )

    instructor = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        verbose_name='Instructor slots',
        help_text="Instructor required.",
        error_messages={'error': "Instructor must required."}
    )
    week_day = models.CharField(max_length=1, choices=week_name)
    start_time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)

    def get_start_time(self):
        from datetime import datetime
        return datetime.strptime(str(self.start_time), '%H:%M:%S')

    def get_end_time(self):
        from datetime import datetime
        return datetime.strptime(str(self.end_time), '%H:%M:%S')

    def get_week_string(self):
        if self.week_day == '1':
            return 'Monday'
        if self.week_day == '2':
            return 'Tuesday'
        if self.week_day == '3':
            return 'Wednesday'
        if self.week_day == '4':
            return 'Thursday'
        if self.week_day == '5':
            return 'Friday'
        if self.week_day == '6':
            return 'Saturday'
        if self.week_day == '7':
            return 'Sunday'
        return ''


class Kids(models.Model):
    kids_name = models.CharField(max_length=300, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    parent = models.ForeignKey(User, on_delete=models.CASCADE)