from django.contrib import admin

# Register your models here.
from StripePayment.models import StripeAccount

admin.site.register(StripeAccount)