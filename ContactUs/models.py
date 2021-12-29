from django.db import models


class ContactUs(models.Model):
    class Meta:
        verbose_name = 'ContactUs'
        verbose_name_plural = "Contact Us"

    full_name = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(max_length=100, null=False, blank=False)
    phone = models.CharField(max_length=25, null=False, blank=False)
    subject = models.CharField(max_length=50, null=False, blank=False)
    message = models.TextField(max_length=500, null=False, blank=False)
    date_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.id} -- {self.full_name}"
