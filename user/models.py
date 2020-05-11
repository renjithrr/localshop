from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager

from utilities.utils import Kw, Konstants

USER_TYPE_CHOICES = Konstants(
    Kw(vendor=1, label='Vendor'),
    Kw(customer=2, label='Customer'),
)


class AppUser(AbstractUser):

    objects = UserManager()
    role = models.IntegerField(choices=USER_TYPE_CHOICES.choices(), null=True)

    def __str__(self):
        return self.username


class DeviceToken(models.Model):
    device_id = models.CharField(max_length=200)
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES.choices(), null=True)
    user_id = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class AppConfigData(models.Model):
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
