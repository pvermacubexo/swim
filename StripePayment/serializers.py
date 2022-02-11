from rest_framework import serializers
from Appointment import models as appointment_model
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StripePaymentSerializer(serializers.ModelSerializer):
    # card_num = serializers.CharField(required=False)
    # exp_month = serializers.CharField(required=False)
    # exp_year = serializers.CharField(required=False)
    # cvc = serializers.CharField(required=False)
    transaction_id = serializers.CharField(required=False)
    booking = serializers.CharField(required=True)
    status = serializers.CharField(required=False)
    payment_type = serializers.CharField(required=True)
    total_amount = serializers.CharField(required=False)
    due_amount = serializers.CharField(required=False)
    paid_amount = serializers.CharField(required=True)

    class Meta:
        model = appointment_model.Transaction
        fields = "__all__"

    def validate(self, attrs):
        try:
            amount = 0
            due_amount = 0
            booking = appointment_model.Booking.objects.get(id=attrs['booking'])
            transaction = appointment_model.Transaction.objects.filter(booking=booking).exclude(
                status=appointment_model.REJECTED).last()
            # booking = appointment_model.Booking.objects.get(id=booking_id)
            ser = RepaymentBookingSeralizer(booking)
            pending_amount = ser.get_pending_amount(booking)
            due_amount = booking.class_instructor.price - booking.get_total_paid - pending_amount
            if int(attrs['paid_amount']) > due_amount:
                raise Exception('Paid amount is greater than due amount. ')
            trns = appointment_model.Transaction.objects.filter(booking=booking).exclude(status='3')
            for i in trns:
                amount += i.paid_amount
            due_amount = booking.class_instructor.price - amount
            attrs['booking'] = booking
            attrs['total_amount'] = booking.class_instructor.price

            # total_amount = int(attrs['total_amount'])
            # paid_amount = int(attrs['paid_amount'])
            # if due_amount == total_amount:
            #     if not (paid_amount > total_amount/2):
            #         raise serializers.ValidationError({'error': "payment fail ! minimum 50% amount require in first payment."})

            if transaction:
                if (not int(due_amount)) and transaction.status != '3':
                    logger.error(f"You already paid full amount for this class.")
                    raise serializers.ValidationError({'error': f"You already paid full amount for this class."})
                elif (int(attrs['paid_amount']) > due_amount) and transaction.status != '3':
                    logger.error(f"Amount should not greater then {due_amount}")
                    raise serializers.ValidationError(
                        {'error': f"Amount should not greater then {due_amount}"})
                attrs['due_amount'] = int(due_amount) - int(attrs['paid_amount'])
            else:
                attrs['due_amount'] = int(attrs['total_amount']) - int(attrs['paid_amount'])

            if int(attrs['paid_amount']) > int(attrs['total_amount']):
                logger.error(f"Amount should not more then ${attrs['total_amount']}.")
                raise serializers.ValidationError({'error': f"Amount should not more then ${attrs['total_amount']}."})
            if int(attrs['paid_amount']) == 0:
                logger.error(f"Amount should greater than or equal to 1.")
                raise serializers.ValidationError({'error': f"Amount should greater than or equal to 1."})
        except appointment_model.Booking.DoesNotExist:
            logger.error(f"{self.context['user']} entered booking Id is {attrs['booking']} which is wrong.")
            raise serializers.ValidationError({'error': 'Invalid Booking ID.'})
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = appointment_model.Transaction
        fields = '__all__'


def transaction_paid_history(obj):
    amount = 0
    transactions = appointment_model.Transaction.objects.filter(booking=obj, status=appointment_model.COMPLETED)
    for transaction in transactions:
        amount += transaction.paid_amount
    return amount


def transaction_pending_history(obj):
    amount = 0
    transactions = appointment_model.Transaction.objects.filter(booking=obj, status=appointment_model.PENDING)
    for transaction in transactions:
        amount += transaction.paid_amount
    return amount


def transaction_reject_history(obj):
    amount = 0
    transactions = appointment_model.Transaction.objects.filter(booking=obj, status=appointment_model.REJECTED)
    for transaction in transactions:
        amount += transaction.paid_amount
    return amount


def transaction_due_history(obj):
    amount = obj.class_instructor.price
    pending = transaction_pending_history(obj)
    complete = transaction_paid_history(obj)
    return amount - int(pending + complete)


def booking_history(obj):
    return appointment_model.Booking.objects.filter(id=obj).first()


def classes(obj):
    return appointment_model.ClassInstructor.objects.filter(id=obj.class_instructor.id).first()


class RepaymentBookingSeralizer(serializers.ModelSerializer):
    due_amount = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    pending_amount = serializers.SerializerMethodField()
    rejected_amount = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    # start_date = serializers.SerializerMethodField()
    # last_date = serializers.SerializerMethodField()
    instuctor = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()
    time_slot = serializers.SerializerMethodField()

    class Meta:
        model = appointment_model.Booking
        fields = '__all__'

    def get_total_amount(self, obj):
        booked_class = classes(obj)
        if booked_class:
            return booked_class.price
        return None

    def get_pending_amount(self, obj):
        pending_amount = transaction_pending_history(obj)
        return pending_amount

    def get_rejected_amount(self, obj):
        pending_amount = transaction_reject_history(obj)
        return pending_amount

    def get_due_amount(self, obj):
        amount = transaction_due_history(obj)
        return amount

    def get_paid_amount(self, obj):
        amount = transaction_paid_history(obj)
        return amount

    def get_class_name(self, obj):
        booking = booking_history(obj.id)
        return booking.class_instructor.title

    # def get_start_date(self, obj):
    #     booking = booking_history(obj.id)
    #     return (booking.last_class.end_time).strftime('%m-%d-%Y') if booking.last_class.end_time else None
    #
    # def get_last_date(self, obj):
    #     booking = booking_history(obj.id)
    #     print(booking.first_class.end_time)
    #     return (booking.first_class.end_time).strftime('%m-%d-%Y') if booking.first_class.end_time else None

    def get_instuctor(self, obj):
        booking = booking_history(obj.id)
        return f"{booking.class_instructor.instructor.first_name}  {booking.class_instructor.instructor.last_name}"

    def get_time_slot(self, obj):
        booking = booking_history(obj.id)
        return booking.class_instructor.time_slot

    def get_total_days(self, obj):
        booking = booking_history(obj.id)
        return booking.class_instructor.total_days
