from django.db import models

# Create your models here.
from user.models import User


class StripeAccount(models.Model):
    Instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    Account_ID = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return self.Account_ID
