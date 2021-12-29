from django.db import models
from django.utils import timezone
from datetime import datetime
from user.models import User


class ClassInstructor(models.Model):
    class Meta:
        verbose_name = 'Class'
        verbose_name_plural = "Classes"
    title = models.CharField(max_length=255)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    time_slot = models.IntegerField()
    total_days = models.IntegerField()
    description = models.CharField(max_length=500)
    price = models.IntegerField(default=0, verbose_name='Fee')
    thumbnail_image = models.ImageField(upload_to='Images/Classes', default='Images/Classes/swim.jpeg', blank=True,
                                        null=True)

    def __str__(self):
        return self.title


BOOKED = '1'
BLOCKED_BY_INSTRUCTOR = '2'
DENIED = '3'
SCHEDULED = '1'
DONE = '2'
CANCELED = '3'

APPOINTMENT_STATUS = (
    (SCHEDULED, 'Scheduled'),
    (DONE, 'Completed'),
    (CANCELED, 'Canceled')
)


class Appointment(models.Model):
    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = "Appointments"
    booking = models.ForeignKey('Appointment.Booking', on_delete=models.CASCADE, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(max_length=1, choices=APPOINTMENT_STATUS, default=SCHEDULED)
    remark = models.CharField(max_length=300, null=True, blank=True)

    @property
    def get_student(self):
        return self.booking.user

    @property
    def get_class(self):
        return self.booking.class_instructor

    def __str__(self):
        return f'{self.booking}'


# DONE = '1'
# NOT_DONE = '2'
PARTIALLY_BOOKED = '0'
BOOKING_COMPLETED = '1'


class Booking(models.Model):
    BOOKING_TYPE_CHOICES = (
        (BOOKED, 'Booked'),
        (DENIED, 'Denied'),
        (BLOCKED_BY_INSTRUCTOR, 'Blocked By Instructor')
    )
    # BOOKING_STATUS_CHOICES = (
    #     (DONE, 'DONE'),
    #     (NOT_DONE, 'NOT DONE')
    # )
    PAYMENT_STATUS_CHOICES = (
        (BOOKING_COMPLETED, 'COMPLETED'),
        (PARTIALLY_BOOKED, 'PARTIALLY BOOKED')
    )
    class_instructor = models.ForeignKey('Appointment.ClassInstructor', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)
    booking_type = models.CharField(max_length=1, choices=BOOKING_TYPE_CHOICES)
    # booking_status = models.CharField(max_length=1, choices=BOOKING_STATUS_CHOICES, default=NOT_DONE)
    booking_payment_status = models.CharField(max_length=1, choices=PAYMENT_STATUS_CHOICES, default=PARTIALLY_BOOKED)
    paper_work = models.BooleanField(null=False, blank=False)

    @property
    def next_class(self):
        appointment = Appointment.objects.filter(booking=self).first()
        return appointment.start_time

    @property
    def last_class(self):
        appointment = Appointment.objects.filter(booking=self).first()
        return appointment.end_time

    @property
    def last_booking(self):
        appointment = Appointment.objects.filter(booking=self).last()
        return appointment.end_time
    @property
    def first_class(self):
        return Appointment.objects.filter(booking=self).order_by('-start_time').first()

    @property
    def get_appointment(self):
        appointments = Appointment.objects.filter(booking=self).order_by('start_time')
        return appointments

    @property
    def payment_status(self):
        is_status = ''
        transactions = Transaction.objects.filter(booking=self)
        for f in transactions:
            if f.status == '1':
                is_status = 'PENDING'
                break
            if f.status == '2':
                is_status = 'COMPLETED'
        return is_status

    @property
    def payment_type(self):
        is_status = ''
        transactions = Transaction.objects.filter(booking=self)
        for f in transactions:
            if f.status == '1':
                is_status = 'CASH'
                break
            if f.status == '2':
                is_status = 'CARD'
        return is_status

    @property
    def appointment_count(self):
        return Appointment.objects.filter(booking=self).count()

    @property
    def appointment_complete(self):
        return Appointment.objects.filter(booking=self, start_time__lte=datetime.now()).count()

    def is_paper_work(self):
        if self.paper_work:
            return 'DONE'
        else:
            return 'NOT DONE'

    def get_booking_payment_status(self):
        if int(self.booking_payment_status) == 0:
            return 'PARTIALLY PAID'
        else:
            return 'FULLY PAID'

    @property
    def transaction(self):
        return Transaction.objects.filter(booking=self).last()

    @property
    def transactions(self):
        return Transaction.objects.filter(booking=self)

    @property
    def get_total_paid(self):
        total_amount = 0
        transactions = Transaction.objects.filter(booking=self, status=COMPLETED)
        for i in transactions:
            total_amount += i.paid_amount
        return total_amount

    @property
    def get_total_due(self):
        total_amount = 0
        transactions = Transaction.objects.filter(booking=self, status=COMPLETED)
        for i in transactions:
            total_amount += i.paid_amount
        return self.class_instructor.price - total_amount

    def __str__(self):
        return f"{self.id} -- {self.user.get_full_name()} - Booked {self.class_instructor.instructor.get_full_name()}'s Class"


PENDING = '1'
COMPLETED = '2'
REJECTED = '3'
CASH = '1'
CARD = '2'


class Transaction(models.Model):
    PAYMENT_STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (REJECTED, 'Rejected')
    )
    PAYMENT_TYPE_CHOICES = (
        (CASH, 'Cash'),
        (CARD, 'Card')
    )
    booking = models.ForeignKey('Appointment.Booking', on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=50, null=False, blank=False)
    status = models.CharField(max_length=1, choices=PAYMENT_STATUS_CHOICES)
    payment_type = models.CharField(max_length=1, choices=PAYMENT_TYPE_CHOICES)
    total_amount = models.IntegerField()
    paid_amount = models.IntegerField()
    due_amount = models.IntegerField()
    payment_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} -- {self.booking.user.get_full_name()} -- {self.paid_amount} -- {self.payment_type}"

    def get_payment_type(self):
        if int(self.payment_type) == 1:
            return 'CASH'
        else:
            return 'CARD'

