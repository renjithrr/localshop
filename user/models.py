from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from localshop.settings.storage_backends import PublicMediaStorage
from utilities.utils import Kw, Konstants

USER_TYPE_CHOICES = Konstants(
    Kw(vendor=1, label='Vendor'),
    Kw(customer=2, label='Customer'),
)


class AppUser(AbstractUser):

    objects = UserManager()
    role = models.IntegerField(choices=USER_TYPE_CHOICES.choices(), blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    account_name = models.CharField(max_length=30, blank=True, null=True)
    ifsc_code = models.CharField(max_length=15, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)

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


class Shop(models.Model):
    user = models.ForeignKey(AppUser, related_name='user_shops', on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=30, blank=True, null=True)
    shop_name = models.CharField(max_length=50, blank=True, null=True)
    business_name = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    gst_reg_number = models.CharField(max_length=50, blank=True, null=True)
    gst_image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
