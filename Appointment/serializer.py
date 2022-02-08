from rest_framework import serializers
from user.models import User
from datetime import date, datetime
from .models import ClassInstructor, Appointment, Booking
from django.contrib.sites.shortcuts import get_current_site

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ClassInstructorSerializer(serializers.ModelSerializer):
    # time_slot=serializers.CharField(max_length=10)
    # def validate_time_slot(self, time_slot):
    #     time_slot=int(time_slot)
    #     if isinstance(time_slot, int):
    #         return time_slot
    #     else:
    #         raise serializers.ValidationError('Time Slot should in minutes')

    class Meta:
        model = ClassInstructor
        fields = '__all__'
        read_only_fields = ('instructor',)


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'


class BookingPostSerializer(serializers.Serializer):
    instructor = serializers.IntegerField()
    class_instructor = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    booked_by = serializers.CharField(required=False)

    def validate_instructor(self, instructor_id):
        try:
            instructor = User.objects.get(id=instructor_id)
        except User.DoesNotExist:
            logger.warning(f"User is not Exist with this ID = {instructor_id}")
            raise serializers.ValidationError('Instructor not found.')
        return instructor

    def validate_class_instructor(self, class_instructor_id):
        try:
            instructor = ClassInstructor.objects.get(id=class_instructor_id)
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class is not Exist with this ID = {class_instructor_id}")
            raise serializers.ValidationError('ClassLevel not found.')
        return instructor


class CheckAvailabilityPostSerializer(serializers.Serializer):
    instructor = serializers.IntegerField()
    class_instructor = serializers.IntegerField()
    start_datetime = serializers.DateTimeField()
    should_book = serializers.BooleanField(default=False)

    def validate_instructor(self, instructor_id):
        try:
            return User.objects.get(id=instructor_id)
        except User.DoesNotExist:
            logger.warning(f"User is not Exist with this ID = {instructor_id}")
            raise serializers.ValidationError('Instructor not found.')

    def validate_class_instructor(self, class_instructor_id):
        try:
            class_instructor = ClassInstructor.objects.get(id=class_instructor_id)
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class is not Exist with this ID = {class_instructor_id}")
            raise serializers.ValidationError({'class_level': 'ClassLevel not found.'})
        return class_instructor


class GetSlotsSerializer(serializers.Serializer):
    class_instructor = serializers.IntegerField()
    instructor = serializers.IntegerField()
    date = serializers.DateField()

    def validate_instructor(self, instructor_id):
        try:
            instructor = User.objects.get(id=instructor_id)
        except User.DoesNotExist:
            logger.warning(f"User is not Exist with this ID = {instructor_id}")
            raise serializers.ValidationError({'instructor': 'Instructor not found.'})
        return instructor

    def validate_class_instructor(self, class_instructor_id):
        try:
            class_instructor = ClassInstructor.objects.get(id=class_instructor_id)
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class is not Exist with this ID = {class_instructor_id}")
            raise serializers.ValidationError({'class_level': 'ClassLevel not found.'})
        return class_instructor


class ClassInstructorInfoSerializer(serializers.ModelSerializer):
    class_instructor = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'

    def get_class_instructor(self, obj):
        return obj.class_instructor.instructor.get_full_name()


class ClassGetSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    appointments = serializers.SerializerMethodField()

    class Meta:
        model = ClassInstructor
        fields = '__all__'

    def get_instructor(self, obj):
        return obj.instructor.get_full_name()

    def get_appointments(self, obj):
        appointments = Appointment.objects.filter(booking__class_instructor=obj)
        appointments_list = {}
        for appointment in appointments:
            appointments_list.update({f"{appointment.start_time.date()}":
                                          {'start_time': appointment.start_time.time().strftime("%I:%M %p"),
                                           'end_time': appointment.end_time.time().strftime("%I:%M %p")}})
        return appointments_list


class InstructorClassGetSerializer(serializers.ModelSerializer):
    thumbnail_image = serializers.SerializerMethodField()
    instructor = serializers.SerializerMethodField()

    class Meta:
        model = ClassInstructor
        fields = '__all__'

    def get_thumbnail_image(self, obj):
        request = self.context.get('request')
        photo_url = obj.thumbnail_image.url
        return request.build_absolute_uri(photo_url)

    def get_instructor(self, obj):
        return obj.instructor.get_full_name()


class GetDateTimeSerializer(serializers.Serializer):
    class_instructor = serializers.IntegerField()
    start_date = serializers.DateField()

    def validate_class_instructor(self, class_instructor_id):
        try:
            class_instructor = ClassInstructor.objects.get(id=class_instructor_id)
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class is not Exist with this ID = {class_instructor_id}")
            raise serializers.ValidationError({'class_level': 'ClassLevel not found.'})
        return class_instructor

    def validate_start_date(self, obj):
        if obj < date.today():
            logger.warning(f"Previous date is not allowed.")
            raise serializers.ValidationError("Previous date is not allowed.")
        return obj


class BookClassInstructorSerializer(serializers.Serializer):
    class_instructor = serializers.CharField()
    date_time = serializers.DateTimeField()
    paper_work = serializers.BooleanField(required=True)

    def validate_class_instructor(self, class_instructor_id):
        try:
            instructor = ClassInstructor.objects.get(id=class_instructor_id)
            return instructor
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class is not Exist with this ID = {class_instructor_id}")
            raise serializers.ValidationError('Invalid Lesson ID.')

    def validate_paper_work(self, paper_work):
        if not paper_work:
            raise serializers.ValidationError('Paper Work is required.')
        return paper_work


# todo
# Fix view details at request.build_absolute_uri('/')[:-1]/instructor/trainee/6
#


class CheckInstructorAvailableSerializer(serializers.Serializer):
    instructor = serializers.IntegerField()

    # date = serializers.DateField()

    def validate_instructor(self, obj):
        try:
            instructor = User.objects.get(id=obj)
        except User.DoesNotExist:
            logger.warning(f"Instructor is not Exist with this ID = {obj}")
            raise serializers.ValidationError('Invalid Instructor ID.')
        return instructor.id

    # def validate_date(self, obj):
    #     if obj < date.today():
    #         raise serializers.ValidationError("Invalid Date")
    #     return obj


# ======================== Individual Booking Serializer Implementation =================

class IndividualTimeSlotsSerializer(serializers.Serializer):
    class_instructor = serializers.IntegerField()
    date_list = serializers.ListField()

    def validate_class_instructor(self, obj):
        try:
            class_instructor = ClassInstructor.objects.get(id=obj)
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class is not Exist with this ID = {obj}")
            raise serializers.ValidationError('Invalid Class ID.')
        return class_instructor

    def validate_date_list(self, date_list):
        try:
            date_list = [datetime.strptime(valid_date, '%Y-%m-%d').date() for valid_date in date_list]
        except Exception:
            logger.warning(f"Invalid date format. You should try yy-mm-dd format.")
            raise serializers.ValidationError('Invalid date format. You should try yy-mm-dd format')
        for date_validate in date_list:
            if date_validate < date.today():
                logger.warning(f"Previous Date not allowed. '{date_validate}'")
                raise serializers.ValidationError(f"Previous date not allowed.")
        return date_list


class IndividualBookingSerializer(serializers.Serializer):
    class_instructor = serializers.IntegerField()
    datetime_list = serializers.ListField()
    paper_work = serializers.BooleanField(required=True)

    def validate_class_instructor(self, obj):
        try:
            class_instructor = ClassInstructor.objects.get(id=obj)
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class is not Exist with this ID = {obj}")
            raise serializers.ValidationError('Invalid Class ID.')
        return class_instructor

    def validate_datetime_list(self, datetime_list):
        try:
            datetime_list = [datetime.strptime(valid_date, '%Y-%m-%dT%H:%M:%S') for valid_date in datetime_list]
        except Exception:
            logger.warning(f"Invalid date format.")
            raise serializers.ValidationError('Invalid date format. You should try yy-mm-ddThh:mm:ss format')
        for date_validate in datetime_list:
            if date_validate.date() < date.today():
                raise serializers.ValidationError(f"Previous date not allowed.")
        return datetime_list


class AppointmentScheduleSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    profile_img = serializers.SerializerMethodField()
    mobile_no = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = '__all__'

    def get_instructor(self, obj):
        return obj.booking.class_instructor.instructor.get_full_name()

    def get_address(self, obj):
        return obj.booking.class_instructor.instructor.address

    def get_title(self, obj):
        return obj.booking.class_instructor.title

    def get_profile_img(self, obj):
        print("====================", obj)
        request = self.context['request']
        path = get_current_site(request=request).domain
        return "http://" + path + '/media/' + str(
            obj.booking.class_instructor.instructor.profile_img)  # todo: fix this jugaad

    def get_mobile_no(self, obj):
        return obj.booking.class_instructor.instructor.mobile_no

    def get_start_time(self, obj):
        return obj.start_time.strftime("%B %d %Y %I:%M %p")

    def get_end_time(self, obj):
        return obj.end_time.strftime("%I:%M %p")
