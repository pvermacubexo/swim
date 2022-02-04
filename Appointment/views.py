import copy
import json
import logging
from datetime import datetime, timedelta
import pytz
import requests

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from SharkDeck.constants import user_constants
from user import models as user_model
from user.decorators import authorize
from user.models import User, Kids
from .models import Appointment, ClassInstructor, BLOCKED_BY_INSTRUCTOR, BOOKED, Booking
from .serializer import BookingPostSerializer, CheckAvailabilityPostSerializer, \
    GetSlotsSerializer, AppointmentSerializer, ClassInstructorSerializer, InstructorClassGetSerializer, \
    GetDateTimeSerializer, BookClassInstructorSerializer, ClassGetSerializer, CheckInstructorAvailableSerializer, \
    IndividualTimeSlotsSerializer, IndividualBookingSerializer, AppointmentScheduleSerializer
from StripePayment.serializers import  RepaymentBookingSeralizer
from Appointment import models as appointment_model
# Get an instance of a logger
logger = logging.getLogger(__name__)


class ClassInstructorViewSet(ModelViewSet):
    serializer_class = ClassInstructorSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ClassInstructor.objects.all()

    @authorize([user_constants.Instructor, user_constants.Trainee])
    def get_queryset(self):
        if self.user.user_type == user_constants.Trainee:
            return ClassInstructor.objects.all()
        else:
            return ClassInstructor.objects.filter(instructor=self.user)

    @authorize([user_constants.Instructor])
    def create(self, request, *args, **kwargs):
        serializer = ClassInstructorSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            serializer.validated_data['instructor'] = request.user
            serializer.save()
            logger.info(
                f"Instructor '{request.user}' created Class '{serializer.validated_data['title']}' successfully")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.warning(f"Instructor '{request.user}' Failed to create a Class due to {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClassGetViewSet(APIView):
    @authorize([user_constants.Trainee])
    def get(self, request):
        try:
            parm = int(self.query_params.get('id'))
        except:
            logger.warning(f"{request.user} want to get class Invalid ID='{self.query_params.get('id')}'.")
            return Response({'error': 'Invalid Class ID.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            class_instructor = ClassInstructor.objects.get(id=parm)
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class with this ID='{self.query_params.get('id')}' Does Not Exist.")
            return Response({'error': 'Class Not Found.'})
        serializer = ClassGetSerializer(class_instructor, many=False, context={"request": request})
        if serializer.data:
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.warning(f"Getting Classes Failed due to {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InstructorClassGetViewSet(APIView):
    @authorize([user_constants.Trainee])
    def get(self, request):
        try:
            parm = int(self.query_params.get('id'))
        except ValueError:
            logger.warning(f"Instructor ID must be Integer, You entered Invalid ID = '{self.query_params.get('id')}'")
            return Response({'error': 'Instructor ID must be an Integer'}, status=status.HTTP_400_BAD_REQUEST)

        class_instructor = ClassInstructor.objects.filter(instructor_id=parm).order_by('-id')
        serializer = InstructorClassGetSerializer(class_instructor, many=True, context={"request": request})
        if serializer.data:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            logger.info(f"{class_instructor.iterator} have not created any class yet.")
            return Response({'no_data': f'Instructor = {class_instructor.iterator} does not have any class yet.'},
                            status=status.HTTP_204_NO_CONTENT)


class AppointmentViewSet(ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Appointment.objects.all()

    def dispatch(self, request, *args, **kwargs):
        dispatch = super().dispatch(request, *args, **kwargs)
        if not self.request.user or self.request.user.is_anonymous:
            logger.error(f"User is not Authorized")
            return JsonResponse({'error': 'user is not Authorized'}, status=status.HTTP_403_FORBIDDEN)
        if not (self.request.user.user_type == user_constants.Trainee):
            logger.error(f"{self.request.user} is not Trainee")
            return JsonResponse({'error': 'user is not Trainee'}, status=status.HTTP_400_BAD_REQUEST)
        return dispatch


def check_availability(start_time, instructor, avoid_blocked_time=False):
    if not start_time.tzinfo:
        start_time = start_time.replace(tzinfo=pytz.UTC)
    appointments = Appointment.objects.filter(start_time__date=start_time.date(),
                                              booking__class_instructor__instructor=instructor)
    is_available = True
    for appointment in appointments:
        is_available = not (appointment.start_time <= start_time <= appointment.end_time)
        if avoid_blocked_time and appointment.booking.booking_type == BLOCKED_BY_INSTRUCTOR:
            return True, False
        if not is_available:
            break
    if avoid_blocked_time:
        return is_available, True
    return is_available


class CheckAvailability(APIView):
    def post(self, request):
        ser = CheckAvailabilityPostSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            class_instructor = ClassInstructor.objects.get(instructor=ser.validated_data['instructor'],
                                                           id=ser.validated_data['class_instructor'].id)
        except ClassInstructor.DoesNotExist:
            return Response({'error': "Instructor Does not Exists. "}, status=status.HTTP_400_BAD_REQUEST)
        time_slot = class_instructor.time_slot
        should_book = ser.validated_data.get('should_book')
        booked_time = {}
        is_available = True
        start_date_temp = ser.validated_data['start_datetime']
        end_date_raw = start_date_temp + timedelta(days=class_instructor.total_days)
        while start_date_temp < end_date_raw:
            is_available, should_increment = check_availability(
                start_date_temp, ser.validated_data['instructor'],
                avoid_blocked_time=True)
            if not is_available:
                return Response({'is_available': False})
            if should_increment:
                if should_book:
                    is_available = False
                    Appointment.objects.create(start_time=start_date_temp,
                                               end_time=start_date_temp + timedelta(minutes=time_slot),
                                               class_instructor=class_instructor,
                                               booking_type=BOOKED)
                booked_time[str(start_date_temp.date())] = [start_date_temp.time(),
                                                            (start_date_temp + timedelta(minutes=time_slot)).time()]
                start_date_temp += timedelta(days=1)
            else:
                start_date_temp += timedelta(days=1)
                end_date_raw += timedelta(days=1)
        return Response({'is_available': is_available,
                         'start_date_temp': ser.validated_data['start_datetime'],
                         'end_date_raw': end_date_raw,
                         'booked': booked_time})


class BookInstructor(APIView):

    @authorize([user_constants.Trainee])
    def get(self, request):
        ser = BookingPostSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            class_instructor = ClassInstructor.objects.get(id=ser.validated_data['class_instructor'].id,
                                                           instructor=ser.validated_data['instructor'])
        except ClassInstructor.DoesNotExist:
            logger.warning(f"Class not found with this ID = {ser.validated_data['class_instructor'].id}.")
            return Response({"error": "Class not found."}, status=status.HTTP_400_BAD_REQUEST)
        time_slot = class_instructor.time_slot
        is_available = check_availability(
            ser.validated_data['start_time'], ser.validated_data['instructor'])
        if is_available:
            Appointment.objects.create(start_time=ser.validated_data['start_time'],
                                       end_time=ser.validated_data['start_time'] + timedelta(minutes=time_slot),
                                       class_instructor=class_instructor,
                                       booking_type=BOOKED, booked_by=request.user)
            return Response({'is_available': is_available, 'booked': True})

        return Response({'is_available': is_available})


def get_timeslots(slot, date, instructor):
    raw_date = datetime(date.year, date.month, date.day)
    processing_date = datetime(date.year, date.month, date.day)
    date_range = {}
    while processing_date.date() == raw_date.date():
        av = check_availability(processing_date, instructor)
        date_range[str(processing_date)] = av
        processing_date = processing_date + timedelta(minutes=slot)

    return date_range


class AvailabilitySlots(APIView):
    def get(self, request):
        ser = GetSlotsSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        class_instructor = ser.validated_data['class_instructor']
        try:
            class_instructor = ClassInstructor.objects.get(instructor=ser.validated_data['instructor'],
                                                           id=class_instructor.id)
        except ClassInstructor.DoesNotExist:
            return Response({'error': "Instructor has Class of this class ID."})
        time_slot_result = get_timeslots(class_instructor.time_slot, ser.validated_data['date'],
                                         ser.validated_data['instructor'])
        return Response(time_slot_result)


# def get_daily_timeslots(slot, day_list, profile_user):
#     total_timeslot = []
#     break_time = user_model.BreakTime.objects.filter(instructor=profile_user)
#     # print('break_time', break_time)
#     raw_start = datetime.strptime(str(profile_user.day_start_time), '%H:%M:%S')
#     # print(raw_start)
#     raw_end = datetime.strptime(str(profile_user.day_end_time), '%H:%M:%S')
#     # print(raw_end)
#     while raw_start <= raw_end:
#         total_timeslot.append((raw_start + timedelta(minutes=1)).time())
#         raw_start = raw_start + timedelta(minutes=slot)
#
#     total_timeslot1 = copy.copy(total_timeslot)
#     # print(day_list)
#     for day in day_list:
#         day_str = day.strftime("%A").lower()
#         # print(day_str)
#         for i in break_time:
#             # print(i.week_day)
#             if day_str == 'monday' and i.week_day == '1':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'tuesday' and i.week_day == '2':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'wednesday' and i.week_day == '3':
#                 # print('weekday', i.week_day)
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'thursday' and i.week_day == '4':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'friday' and i.week_day == '5':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'saturday' and i.week_day == '6':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'sunday' and i.week_day == '7':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#     if len(total_timeslot) == 1:
#         print(total_timeslot)
#         # total_timeslot.pop()
#         # print(total_timeslot)
#     if total_timeslot:
#         return total_timeslot
#     return False

# def get_daily_timeslots(slot, day_list, profile_user):
#     total_timeslot = []
#     break_time = user_model.BreakTime.objects.filter(instructor=profile_user)
#     raw_start = datetime.strptime(str(profile_user.day_start_time), '%H:%M:%S')
#     raw_end = datetime.strptime(str(profile_user.day_end_time), '%H:%M:%S')
#     while raw_start <= raw_end:
#         total_timeslot.append((raw_start + timedelta(minutes=1)).time())
#         raw_start = raw_start + timedelta(minutes=slot)
#
#     total_timeslot1 = copy.copy(total_timeslot)
#     for day in day_list:
#         day_str = day.strftime("%A").lower()
#         for i in break_time:
#             if day_str == 'monday' and i.week_day == '1':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'tuesday' and i.week_day == '2':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'wednesday' and i.week_day == '3':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'thursday' and i.week_day == '4':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'friday' and i.week_day == '5':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'saturday' and i.week_day == '6':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#             if day_str == 'sunday' and i.week_day == '7':
#                 for remove_time in total_timeslot1:
#                     single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()
#
#                     if i.start_time <= remove_time <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#                     if i.start_time <= single_slot_end <= i.end_time:
#                         if remove_time in total_timeslot:
#                             total_timeslot.remove(remove_time)
#
#     if len(total_timeslot) == 1:
#         total_timeslot.pop()
#     if total_timeslot:
#         return total_timeslot
#     return False

def get_daily_timeslots(slot, day_list, profile_user):
    total_timeslot = []
    break_time = user_model.BreakTime.objects.filter(instructor=profile_user)
    raw_start = datetime.strptime(str(profile_user.day_start_time), '%H:%M:%S')
    raw_end = datetime.strptime(str(profile_user.day_end_time), '%H:%M:%S')
    while raw_start <= raw_end:
        total_timeslot.append((raw_start + timedelta(minutes=1)).time())
        raw_start = raw_start + timedelta(minutes=slot)

    total_timeslot1 = copy.copy(total_timeslot)
    for day in day_list:
        day_str = day.strftime("%A").lower()
        for i in break_time:
            if day_str == 'monday' and i.week_day == '1':
                for remove_time in total_timeslot1:
                    single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()

                    if i.start_time <= remove_time <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)
                    if i.start_time <= single_slot_end <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)

            if day_str == 'tuesday' and i.week_day == '2':
                for remove_time in total_timeslot1:
                    single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()

                    if i.start_time <= remove_time <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)
                    if i.start_time <= single_slot_end <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)

            if day_str == 'wednesday' and i.week_day == '3':
                for remove_time in total_timeslot1:
                    single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()

                    if i.start_time <= remove_time <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)
                    if i.start_time <= single_slot_end <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)

            if day_str == 'thursday' and i.week_day == '4':
                for remove_time in total_timeslot1:
                    single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()

                    if i.start_time <= remove_time <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)
                    if i.start_time <= single_slot_end <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)

            if day_str == 'friday' and i.week_day == '5':
                for remove_time in total_timeslot1:
                    single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()

                    if i.start_time <= remove_time <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)
                    if i.start_time <= single_slot_end <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)

            if day_str == 'saturday' and i.week_day == '6':
                for remove_time in total_timeslot1:
                    single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()

                    if i.start_time <= remove_time <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)
                    if i.start_time <= single_slot_end <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)

            if day_str == 'sunday' and i.week_day == '7':
                for remove_time in total_timeslot1:
                    single_slot_end = (datetime.strptime(str(remove_time), '%H:%M:%S') + timedelta(minutes=slot)).time()

                    if i.start_time <= remove_time <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)
                    if i.start_time <= single_slot_end <= i.end_time:
                        if remove_time in total_timeslot:
                            total_timeslot.remove(remove_time)

    if len(total_timeslot) == 1:
        total_timeslot.pop()
    if total_timeslot:
        return total_timeslot
    return False


def get_common_slots(class_instructor, start_date, profile_user):
    # format = '%I:%M %p'
    day_list = []
    pair_time = []
    available_week = week_available(class_instructor.instructor.id)
    week_str = start_date.strftime("%A").lower()
    if not (week_str in available_week):
        return False, False
    end_date = start_date + timedelta(days=class_instructor.total_days)
    while start_date < end_date:
        if start_date.strftime("%A").lower() in available_week:
            day_list.append(start_date)
        else:
            end_date += timedelta(days=1)
        start_date += timedelta(days=1)
    time_list = get_daily_timeslots(class_instructor.time_slot, day_list, profile_user)
    if not time_list:
        return False, False
    time_list = (sorted(time_list))
    for day in day_list:
        for start_time in time_list:
            date_time = datetime.combine(day, start_time)
            if not check_availability(date_time, class_instructor.instructor):
                time_list.remove(start_time)
    time_count = 1
    for single_time in time_list:
        if time_count < len(time_list):
            pair_time.append(
                f"{(datetime.strptime(str(single_time), '%H:%M:%S')).time()} - "
                f"{((datetime.strptime(str(single_time), '%H:%M:%S')) + timedelta(minutes=class_instructor.time_slot - 1)).time()}")
            time_count += 1
    return day_list, pair_time


# def get_common_slots(class_instructor, start_date, profile_user):
#     # format = '%I:%M %p'
#     day_list = []
#     pair_time = []
#     # print(class_instructor.instructor.id)
#     available_week = week_available(class_instructor.instructor.id)
#
#     week_str = start_date.strftime("%A").lower()
#
#     if not (week_str in available_week):
#         return False, False
#     end_date = start_date + timedelta(days=class_instructor.total_days)
#     while start_date < end_date:
#         if start_date.strftime("%A").lower() in available_week:
#             day_list.append(start_date)
#         else:
#             end_date += timedelta(days=1)
#         start_date += timedelta(days=1)
#     # print(start_date)
#     time_list = get_daily_timeslots(class_instructor.time_slot, day_list, profile_user)
#     if not time_list:
#         return False, False
#     time_list = (sorted(time_list))
#     for day in day_list:
#         for start_time in time_list:
#             date_time = datetime.combine(day, start_time)
#             if not check_availability(date_time, class_instructor.instructor):
#                 time_list.remove(start_time)
#     time_count = 1
#     for single_time in time_list:
#         if time_count < len(time_list):
#             pair_time.append(
#                 f"{(datetime.strptime(str(single_time), '%H:%M:%S')).time()} - "
#                 f"{((datetime.strptime(str(single_time), '%H:%M:%S')) + timedelta(minutes=class_instructor.time_slot - 1)).time()}")
#             time_count += 1
#     return day_list, pair_time

class GetDateTimeSlots(APIView):
    def get(self, request):
        serializer = GetDateTimeSerializer(data=request.query_params)
        if serializer.is_valid():
            try:
                class_instructor = ClassInstructor.objects.get(id=serializer.validated_data['class_instructor'].id)
                profile_user = user_model.Profile.objects.get(user=class_instructor.instructor)
            except user_model.Profile.DoesNotExist:
                logger.warning(f"{serializer.validated_data['class_instructor'].instructor} has no Profile. Every "
                               f"Instructor must have own Profile.")
                return Response({'error': 'Invalid Instructor ID.'})
            except ClassInstructor.DoesNotExist:
                logger.warning(f"Class Does not Exist of this  ID = {serializer.validated_data['class_instructor'].id}")
                return Response({'error': 'Invalid Class ID.'})
            day_result, time_result = get_common_slots(class_instructor, serializer.validated_data['start_date'],
                                                       profile_user)
            if not (day_result or time_result):
                return Response({'error': 'Instructor is on Holiday on this day.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'date': day_result, 'time': time_result})
        else:
            return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


# class GetDateTimeSlots(APIView):
#     # @authorize([user_constants.Trainee])
#     def get(self, request):
#         # print(request)
#         serializer = GetDateTimeSerializer(data=request.query_params)
#         if serializer.is_valid():
#             try:
#                 # print(serializer.validated_data['class_instructor'].id)
#                 class_instructor = ClassInstructor.objects.get(id=serializer.validated_data['class_instructor'].id)
#
#                 profile_user = user_model.Profile.objects.get(user=class_instructor.instructor)
#             except user_model.Profile.DoesNotExist:
#                 logger.warning(f"{serializer.validated_data['class_instructor'].instructor} has no Profile. Every "
#                                f"Instructor must have own Profile.")
#                 return Response({'error': 'Invalid Instructor ID.'})
#             except ClassInstructor.DoesNotExist:
#                 logger.warning(f"Class Does not Exist of this  ID = {serializer.validated_data['class_instructor'].id}")
#                 return Response({'error': 'Invalid Class ID.'})
#             # print(class_instructor)
#             # print(type(class_instructor))
#             # print(profile_user)
#             day_result, time_result = get_common_slots(class_instructor, serializer.validated_data['start_date'],
#                                                        profile_user)
#
#             if not (day_result or time_result):
#                 return Response({'error': 'Instructor is Holiday on this day.'}, status=status.HTTP_400_BAD_REQUEST)
#             return Response({'date': day_result, 'time': time_result})
#         else:
#             return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


def CheckBooking(checking_time, class_instructor):
    try:
        instructor_class = ClassInstructor.objects.get(id=class_instructor)
    except ClassInstructor.DoesNotExist:
        return False
    is_booking = True
    appointments = Appointment.objects.filter(booking__class_instructor__id=class_instructor,
                                              start_time=checking_time)
    for appointment in appointments:
        is_booking = not (appointment.start_time <= checking_time <= appointment.end_time or
                          appointment.start_time <= checking_time + timedelta(minutes=instructor_class.time_slot) <=
                          appointment.end_time)

    return is_booking


def Available_instructor(booking_time, class_instructor):
    appointments = Appointment.objects.filter(booking__class_instructor_id=class_instructor,
                                              start_time=booking_time)
    is_available = True
    for appointment in appointments:
        is_available = not (appointment.start_time <= booking_time - timedelta(minutes=1) <= appointment.end_time)
        if not is_available:
            return is_available

    return is_available


def week_available(instructor_id):
    week_list = []
    try:
        instructor = user_model.Profile.objects.get(user_id=instructor_id)
    except user_model.User.DoesNotExist:
        return False
    if instructor.monday:
        week_list.append('monday')
    if instructor.tuesday:
        week_list.append('tuesday')
    if instructor.wednesday:
        week_list.append('wednesday')
    if instructor.thursday:
        week_list.append('thursday')
    if instructor.friday:
        week_list.append('friday')
    if instructor.saturday:
        week_list.append('saturday')
    if instructor.sunday:
        week_list.append('sunday')
    return week_list


class BookClassInstructor(APIView):
    # @authorize([user_constants.Trainee])
    def get(self, request):
        serializer = BookClassInstructorSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        available_week = week_available(serializer.validated_data['class_instructor'].instructor.id)
        if not (datetime.strptime(str(serializer.validated_data['date_time'].date()), '%Y-%m-%d').date().strftime(
                '%A').lower() in available_week):
            logger.warning(
                f"{serializer.validated_data['class_instructor'].instructor} Holiday on {serializer.validated_data['date_time'].date()}")
            return Response({'error': f"Instructor is Holiday on {serializer.validated_data['date_time'].date()}"},
                            status=status.HTTP_400_BAD_REQUEST)
        class_instructor_obj = serializer.validated_data['class_instructor']
        kids_obj = serializer.validated_data['kids_id']
        is_available = Available_instructor(serializer.validated_data['date_time'],
                                            serializer.validated_data['class_instructor'])
        is_booking = CheckBooking(serializer.validated_data['date_time'],
                                  serializer.validated_data['class_instructor'].id)
        day_list = []
        booked_slots = []
        if is_available and is_booking:
            try:
                class_instructor = ClassInstructor.objects.get(id=class_instructor_obj.id)
                kids = Kids.objects.get(id=kids_obj)
            except ClassInstructor.DoesNotExist:
                logger.warning(f"Class Does not Exist of this  ID = {serializer.validated_data['class_instructor'].id}")
                return Response({"error": "Class not found."}, status=status.HTTP_400_BAD_REQUEST)
            end_time = serializer.validated_data['date_time'] + timedelta(days=class_instructor.total_days,
                                                                          minutes=class_instructor.time_slot)
            start_time = serializer.validated_data['date_time']
            time_slot = class_instructor.time_slot
            while len(day_list) < class_instructor.total_days:
                if datetime.strptime(str(start_time.date()), '%Y-%m-%d').date().strftime(
                        '%A').lower() in available_week:
                    day_list.append(start_time)
                    start_time += timedelta(days=1)
                else:
                    start_time += timedelta(days=1)

            reqested_user = User.objects.get(email=request.session["email"])
            booking = Booking.objects.create(class_instructor=class_instructor, user=reqested_user, booking_type=BOOKED,
                                             paper_work=serializer.data['paper_work'], kids=kids)
            for day in day_list:
                start_time = datetime.combine(day, serializer.validated_data['date_time'].time())
                appointment = Appointment.objects.create(start_time=start_time,
                                                         end_time=start_time + timedelta(
                                                             minutes=serializer.validated_data[
                                                                         'class_instructor'].time_slot - 1),
                                                         booking=booking)

                booked_slots.append(appointment.start_time)
            start_time_12hour = start_time
            # start_time_12hour = start_time.strftime("%H:%M %p")
            end_time_12hour = (start_time + timedelta(minutes=time_slot - 1))
            # end_time_12hour = (start_time + timedelta(minutes=time_slot)).strftime("%H:%M %p")
            full_name = class_instructor.instructor.first_name + " " + class_instructor.instructor.last_name
            appointments = Appointment.objects.filter(booking=booking)
            appointments_list = {}
            for appointment in appointments:
                appointments_list.update({f"{appointment.start_time.date().strftime('%b, %d %Y')}":
                                              {'start_time': appointment.start_time.time().strftime("%I:%M %p"),
                                               'end_time': appointment.end_time.time().strftime("%I:%M %p")}})
            return Response({
                'booking': booking.id,
                'class_instructor': class_instructor.title,
                'class_instructor_id': class_instructor.id,
                'kids_name': kids.kids_name,
                'paper_work': booking.paper_work,
                'instructor': full_name,
                'instructor_id': class_instructor.instructor.id,
                'booked_from': appointments.first().start_time.date().strftime("%b, %d %Y"),
                'appointments': appointments_list,
                'fee': class_instructor.price,
                'total_days': class_instructor.total_days,
                'booking_to': appointments.last().end_time.date().strftime("%b, %d %Y"),
                'start_time': start_time_12hour,
                'end_time': end_time_12hour,
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Instructor is busy on this time, Please Select another time.'},
                        status=status.HTTP_400_BAD_REQUEST)


class CheckInstructorViewSet(APIView):
    @authorize([user_constants.Trainee])
    def get(self, request):
        serializer = CheckInstructorAvailableSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        available_week = week_available(serializer.data['instructor'])
        if not available_week:
            return Response({'error': f"Instructor Does not Exist."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(available_week, status=status.HTTP_200_OK)


# ============== Individual Booking View sets Implementation ============================
def individual_daily_timeslots(slot, date_filter, user_profile):
    time_list = []
    time_dict = {}
    pair_time = []
    time_count = 0
    appointments = Appointment.objects.filter(booking__class_instructor__instructor=user_profile.user,
                                              start_time__date=date_filter)
    try:
        instructor = user_model.WeekTimeSlots.objects.get(instructor=user_profile)
    except user_model.WeekTimeSlots:
        return Response({'error': 'Instructor not found.'}, status=status.HTTP_400_BAD_REQUEST)
    week_day = datetime.strptime(date_filter, '%Y-%m-%d').date().strftime('%A').lower()
    break_time = user_model.BreakTime.objects.filter(instructor=user_profile)
    raw_start = datetime.strptime(str(user_profile.day_start_time), '%H:%M:%S')
    raw_end = datetime.strptime(str(user_profile.day_end_time), '%H:%M:%S')

    while raw_start <= raw_end:
        time_list.append(raw_start + timedelta(minutes=1))
        raw_start += timedelta(minutes=slot)
    for appointment in appointments:
        for remove_time in time_list:
            if appointment.start_time.time() <= remove_time.time() <= appointment.end_time.time():
                time_list.remove(remove_time)
    total_timeslot1 = copy.copy(time_list)
    for i in break_time:
        if week_day == 'monday' and i.week_day == '1':
            for remove_time in total_timeslot1:
                single_slot_end = (
                            datetime.strptime(str(remove_time.time()), '%H:%M:%S') + timedelta(minutes=slot)).time()
                if i.start_time <= remove_time.time() <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
                if i.start_time <= single_slot_end <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
        if week_day == 'tuesday' and i.week_day == '2':
            for remove_time in total_timeslot1:
                single_slot_end = (
                            datetime.strptime(str(remove_time.time()), '%H:%M:%S') + timedelta(minutes=slot)).time()
                if i.start_time <= remove_time.time() <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
                if i.start_time <= single_slot_end <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
        if week_day == 'wednesday' and i.week_day == '3':
            for remove_time in total_timeslot1:
                single_slot_end = (
                            datetime.strptime(str(remove_time.time()), '%H:%M:%S') + timedelta(minutes=slot)).time()
                if i.start_time <= remove_time.time() <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
                if i.start_time <= single_slot_end <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
        if week_day == 'thursday' and i.week_day == '4':
            for remove_time in total_timeslot1:
                single_slot_end = (
                            datetime.strptime(str(remove_time.time()), '%H:%M:%S') + timedelta(minutes=slot)).time()
                if i.start_time <= remove_time.time() <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
                if i.start_time <= single_slot_end <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
        if week_day == 'friday' and i.week_day == '5':
            for remove_time in total_timeslot1:
                single_slot_end = (
                            datetime.strptime(str(remove_time.time()), '%H:%M:%S') + timedelta(minutes=slot)).time()
                if i.start_time <= remove_time.time() <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
                if i.start_time <= single_slot_end <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
        if week_day == 'saturday' and i.week_day == '6':
            for remove_time in total_timeslot1:
                single_slot_end = (
                            datetime.strptime(str(remove_time.time()), '%H:%M:%S') + timedelta(minutes=slot)).time()
                if i.start_time <= remove_time.time() <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
                if i.start_time <= single_slot_end <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
        if week_day == 'sunday' and i.week_day == '7':
            for remove_time in total_timeslot1:
                single_slot_end = (
                            datetime.strptime(str(remove_time.time()), '%H:%M:%S') + timedelta(minutes=slot)).time()
                if i.start_time <= remove_time.time() <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
                if i.start_time <= single_slot_end <= i.end_time:
                    if remove_time in time_list:
                        time_list.remove(remove_time)
    for single_time in time_list:
        time_count += 1
        if time_count < len(time_list):
            pair_time.append(
                f"{single_time.time()} - "
                f"{(single_time + timedelta(minutes=slot - 1)).time()}")
    time_dict[date_filter] = pair_time if pair_time else None
    return time_dict


def individual_common_slot(class_instructor, date_list, profile_user):
    time_list = []
    available_week = week_available(class_instructor.instructor.id)
    for single_date in date_list:
        if not (datetime.strptime(single_date, '%Y-%m-%d').date().strftime('%A').lower() in available_week):
            logger.warning(f"{class_instructor.instructor} Holiday on {single_date}")
            return False, f'{single_date}'
        time_list.append(individual_daily_timeslots(class_instructor.time_slot, single_date, profile_user))

    return time_list


class GetIndividualTimeSlots(APIView):
    # @authorize([user_constants.Trainee])
    def post(self, request):
        serializer = IndividualTimeSlotsSerializer(data=request.data)
        if serializer.is_valid():
            try:
                class_instructor = ClassInstructor.objects.get(id=serializer.initial_data['class_instructor'])
                # print(class_instructor)
                user_profile = user_model.Profile.objects.get(user=class_instructor.instructor)
            except ClassInstructor.DoesNotExist:
                logger.warning(f"Class not found with this ID = {serializer.initial_data['class_instructor']}")
                return Response({'error': 'Invalid Class ID.'}, status=status.HTTP_400_BAD_REQUEST)
            except user_model.Profile.DoesNotExist:
                logger.warning(f"{serializer.validated_data['class_instructor'].instructor} has no Profile. Every "
                               f"Instructor must have own Profile.")
                return Response({'error': 'Instructor Profile not matched.'}, status=status.HTTP_400_BAD_REQUEST)

            if not (class_instructor.total_days == len(serializer.initial_data['date_list'])):
                logger.warning(f"You should select {int(class_instructor.total_days)} days")
                return Response(
                    {'error': f"You should select {int(class_instructor.total_days)} days."},
                    status=status.HTTP_400_BAD_REQUEST)

            common_slot = individual_common_slot(class_instructor, serializer.initial_data['date_list'], user_profile)
            if not common_slot[0]:
                # return Response({'error': f"{class_instructor.instructor} Leave on {common_slot[1]} "},
                return Response({'error': f"Instructor is Leave on {common_slot[1]} "},
                                status=status.HTTP_400_BAD_REQUEST)

            # dateListFormat = {}
            # common_slot = list(common_slot)
            # date_format = serializer.initial_data['date_list']
            # for dateFormat in date_format:
            #     dateListFormat[dateFormat] = str((datetime.strptime(dateFormat, "%Y-%m-%d").date()).strftime("%b %d %Y"))
            # common_slot.append(dateListFormat)
            return Response(common_slot, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class IndividualBookingViewSet(APIView):
    # @authorize([user_constants.Trainee])
    def post(self, request):
        serializer = IndividualBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        class_instructor = serializer.validated_data['class_instructor']
        kids_id = serializer.validated_data['kids_id']
        kids_obj = Kids.objects.get(id=kids_id)
        print(kids_obj.kids_name)
        datetime_list = serializer.initial_data['datetime_list']
        if not (class_instructor.total_days == len(datetime_list)):
            logger.warning(f"You select {len(datetime_list)} day of class, should select "
                           f"{int(class_instructor.total_days) - int(len(datetime_list))} day more.")
            return Response(
                {'error': f"You select {len(datetime_list)} day of class, should select "
                          f"{int(class_instructor.total_days) - int(len(datetime_list))} day "
                          f"more."},
                status=status.HTTP_400_BAD_REQUEST)
        if not (class_instructor.total_days < int(len(serializer.initial_data['datetime_list']) + 1)):
            logger.warning(f"You selected {len(serializer.initial_data['datetime_list'])} days.You should choose only "
                           f"{class_instructor.total_days}")
            return Response({'error': f"You selected {len(serializer.initial_data['datetime_list'])} "
                                      f"days.You should choose only {class_instructor.total_days}"},
                            status=status.HTTP_400_BAD_REQUEST)
        available_day = week_available(class_instructor.instructor.id)
        for date_time in datetime_list:
            date_filter = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S')
            if not datetime.strptime(str(date_filter.date()), '%Y-%m-%d').date().strftime(
                    '%A').lower() in available_day:
                return Response({'error': f'Instructor not available on date {date_time}'})
            date_time = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S')
            date_time = date_time.replace(tzinfo=pytz.UTC)
            if not (Available_instructor(date_time, class_instructor)):
                logger.warning(f"Instructor = {class_instructor.instructor} is Not Available on '{date_time}'")
                return Response({'error': 'Instructor Not Available'}, status=status.HTTP_400_BAD_REQUEST)
            if not (CheckBooking(date_time, class_instructor.id)):
                logger.warning(f"Instructor = {class_instructor.instructor} is Not Available on '{date_time}'")
                return Response({'error': 'Instructor Not Available'}, status=status.HTTP_400_BAD_REQUEST)
        reqested_user = User.objects.get(email='test@ymail.com')
        booking = Booking.objects.create(class_instructor=class_instructor,
                                         user= reqested_user, booking_type=BOOKED,
                                         paper_work=serializer.validated_data['paper_work'], kids=kids_obj)
        for date_time in datetime_list:
            date_time = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S')
            date_time = date_time.replace(tzinfo=pytz.UTC)
            try:
                Appointment.objects.create(start_time=date_time,
                                           end_time=date_time + timedelta(minutes=class_instructor.time_slot - 1),
                                           booking=booking)
            except Exception:
                booking.delete()
                logger.warning(f"Booking Failed due to Appointment creating fail.")
                return Response({'error': 'Booking failed.'}, status=status.HTTP_400_BAD_REQUEST)
        appointments = Appointment.objects.filter(booking=booking)
        booked_appointment = []
        if appointments:
            for appointment in appointments:
                appointmenat_date = appointment.start_time.date().strftime("%b, %d %Y")
                booked_appointment.append(
                    {f'{appointmenat_date}': f'{appointment.start_time.time().strftime("%I:%M %p")} to '
                                             f'{appointment.end_time.time().strftime("%I:%M %p")}'})

        full_name = class_instructor.instructor.first_name + " " + class_instructor.instructor.last_name
        return Response({
            'booking': booking.id,
            'class_instructor_id': class_instructor.id,
            'total_days': class_instructor.total_days,
            'fee': class_instructor.price,
            'class_instructor': class_instructor.title,
            'instructor': full_name,
            'kids_name': kids_obj.kids_name,
            'instructor_id': class_instructor.instructor.id,
            'dateTime': booked_appointment,
        }, status=status.HTTP_200_OK)


class BookingDelete(APIView):
    @authorize([user_constants.Trainee])
    def post(self, request):
        try:
            Booking.objects.get(id=int(request.data['id'])).delete()
            return Response({'message': 'Booking delete successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid ID'}, status=status.HTTP_400_BAD_REQUEST)


# class AppointmentScheduleViewSet(ModelViewSet):
#     serializer_class = AppointmentScheduleSerializer
#     # permission_classes = (IsAuthenticated,)
#     queryset = Appointment.objects.all()
#
#     @authorize([user_constants.Trainee])
#     def get_queryset(self):
#         appointments = Appointment.objects.filter(booking__user=self.user,)
#         # serializer.is_valid(raise_exception=True)
#         aop = {'asa': appointments}
#         return aop

class AppointmentScheduleViewSet(APIView):
    # @authorize([user_constants.Trainee])

    def get(self, request):
        appointments = Appointment.objects.filter(
            booking__user=User.objects.get(email=request.session['email'])).order_by('start_time')
        # print(appointments..booking.kids.kids_name)
        if appointments:
            prev_appointment = AppointmentScheduleSerializer(
                appointments.filter(start_time__lt=datetime.now()).order_by('-start_time'), many=True,
                context={'request': request})
            next_appointment = AppointmentScheduleSerializer(appointments.filter(start_time__gt=datetime.now()),
                                                             many=True, context={'request': request})
            print(next_appointment.data[0])
            if prev_appointment.data or next_appointment.data:
                email = request.session['email']
                obj = User.objects.get(email=email)

                logger.info(f"Appointment Schedule details for {request.user}")
                return render(request,"my_shedule.html",{"user_details": obj,'prev_session': prev_appointment.data, 'next_session': next_appointment.data})
            else:
                logger.info(f"Getting error of Appointment Schedule details due")
                return render(request,"my_shedule.html",{'error': 'Appointment schedule failed'})
        else:
            email = request.session['email']
            obj = User.objects.get(email=email)
            return render(request,"my_shedule.html",{"user_details": obj,'message': 'There is no any Appointment Schedule.'})


