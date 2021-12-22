from django.contrib import admin
from .models import ContactUs


class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone')
    search_fields = ['phone', 'date_time']
    date_hierarchy = 'date_time'

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['date_time', 'email']
        else:
            return []


admin.site.register(ContactUs, ContactUsAdmin)
