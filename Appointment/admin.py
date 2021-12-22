from django.contrib import admin

from .models import Appointment, ClassInstructor, Transaction, Booking


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'start_time', 'end_time', 'status']
    search_fields = ['start_time', 'booked_by', 'booking_type']
    date_hierarchy = 'start_time'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['booking', 'start_time']
        else:
            return []


class ClassInstructorAdmin(admin.ModelAdmin):
    list_display = ('title', 'time_slot', 'total_days', 'price')
    search_fields = ['total_days', 'time_slot', 'price']

    # date_hierarchy = 'created'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['instructor']
        else:
            return []


class BookingAdmin(admin.ModelAdmin):
    list_display = ('class_instructor', 'user', 'booked_at', 'booking_payment_status')
    search_fields = ['user', 'booked_at']
    date_hierarchy = 'booked_at'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['class_instructor', 'user', 'booked_at']
        else:
            return []


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('booking','status', 'payment_type', 'total_amount', 'paid_amount', 'due_amount', 'payment_at')
    search_fields = ['total_amount', 'payment_at', 'due_amount']
    date_hierarchy = 'payment_at'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['booking', 'payment_type', 'payment_at', 'total_amount', 'transaction_id']
        else:
            return []


admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(ClassInstructor, ClassInstructorAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Booking, BookingAdmin)

