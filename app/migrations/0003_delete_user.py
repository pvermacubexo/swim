# Generated by Django 3.1.1 on 2021-12-20 12:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_user_date_of_birth'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
    ]
