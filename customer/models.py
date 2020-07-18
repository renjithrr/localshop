from django.contrib.gis.db import models
from user.models import AuditedModel, AppUser
from utilities.utils import Kw, Konstants

ADDRESS_TYPES = Konstants(
    Kw(home=1, label='Home'),
    Kw(work=2, label='Work'),
    Kw(other=3, label='Other'),
)


class Customer(AuditedModel, models.Model):
    user = models.OneToOneField(AppUser, related_name='customer', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Address(AuditedModel, models.Model):
    customer = models.OneToOneField(Customer, related_name='customer_addresses', on_delete=models.CASCADE)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    long = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    location = models.PointField(blank=True, null=True)
    locality = models.CharField(max_length=30, blank=True, null=True)
    address_type = models.IntegerField(choices=ADDRESS_TYPES.choices(), default=ADDRESS_TYPES.home)
