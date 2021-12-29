from Appointment import models


def get_instructors_trainees(instructor):
    return [booking.user for booking in models.Booking.objects.filter(class_instructor__instructor=instructor)]


def get_instructors_bookings(instructor):
    return models.Booking.objects.filter(class_instructor__instructor=instructor)

def get_instructor_transactions(instructor):
    return models.Transaction.objects.filter(booking__class_instructor__instructor=instructor)

def get_complete_transactions(instructor):
    return models.Transaction.objects.filter(booking__class_instructor__instructor=instructor, status=models.COMPLETED)
def get_pending_transactions(instructor):
    return models.Transaction.objects.filter(booking__class_instructor__instructor=instructor, status=models.PENDING)
