# Generated by Django 3.2.9 on 2022-01-07 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('StripePayment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripeaccount',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]