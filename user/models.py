from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser, User, UserManager

from localshop.settings.storage_backends import PublicMediaStorage
from utilities.utils import Kw, Konstants
from multiselectfield import MultiSelectField
from django.contrib.postgres.fields import JSONField



USER_TYPE_CHOICES = Konstants(
    Kw(vendor=1, label='Vendor'),
    Kw(customer=2, label='Customer'),
    Kw(admin=3, label='Admin'),
)

SHOP_CATEGORY_CHOICES = Konstants(
    Kw(electronics=1, label='Vendor'),
    Kw(customer=2, label='Customer'),
)

SHOP_STATUS_CHOICES = Konstants(
    Kw(approved=1, label='Approved'),
    Kw(rejected=2, label='Rejected'),
    Kw(deleted=3, label='Deleted'),
    Kw(offline=4, label='Offline'),
    Kw(pending=5, label='Pending'),
)

DELIVERY_CHOICES = Konstants(
    Kw(pickup=1, label='Pick up'),
    Kw(self_delivery=2, label='Self delivery'),
    Kw(bulk_delivery=3, label='Bulk delivery'),
    Kw(townie_ship=4, label='Townie ship'),
)

PAYMENT_CHOICES = Konstants(
    Kw(google_pay=1, label='Google pay'),
    Kw(paytm=2, label='Paytm'),
    Kw(credit_card=3, label='Credit card'),
    Kw(debit_card=4, label='Debit card'),
    Kw(cod=5, label='COD')
)


CARD_CHOICES = Konstants(
    Kw(small=1, label='Small'),
    Kw(medium=2, label='Medium'),
    Kw(big=3, label='Big')
)


class AppUser(AbstractUser):

    objects = UserManager()
    role = models.IntegerField(choices=USER_TYPE_CHOICES.choices(), blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    account_name = models.CharField(max_length=30, blank=True, null=True)
    ifsc_code = models.CharField(max_length=15, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    verification_otp = models.CharField(max_length=8, blank=True, null=True)

    def __str__(self):
        return self.username


class AuditedModel(models.Model):
    created_by = models.ForeignKey(AppUser, related_name='+', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(AppUser, related_name='+', on_delete=models.CASCADE, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DeviceToken(models.Model):
    device_id = models.CharField(max_length=200)
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES.choices(), null=True)
    user_id = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class AppConfigData(models.Model):
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)


class ShopCategory(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    fssai = models.BooleanField(default=False)
    card_type = models.IntegerField(choices=CARD_CHOICES.choices(), blank=True, null=True)


    def __str__(self):
        return self.name


class ServiceArea(AuditedModel, models.Model):
    name = models.CharField(max_length=70, blank=True, null=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    long = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    location = models.PointField(default='POINT (0 0)',srid=4326)
    # townie_delivery_start = models.TimeField(blank=True, null=True)
    townie_delivery_end = models.TimeField(blank=True, null=True)
    # self_delivery_start = models.TimeField(blank=True, null=True)
    # self_delivery_end = models.TimeField(blank=True, null=True)


    def __str__(self):
        return str(self.id)


class Shop(AuditedModel, models.Model):
    user = models.ForeignKey(AppUser, related_name='user_shops', on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=30, blank=True, null=True)
    shop_name = models.CharField(max_length=70, blank=True, null=True)
    business_name = models.CharField(max_length=70, blank=True, null=True)
    shop_category = models.ForeignKey(ShopCategory, related_name='category_shops', on_delete=models.CASCADE,
                                      blank=True, null=True)
    gst_reg_number = models.CharField(max_length=50, blank=True, null=True)
    gst_image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
    fssai = models.CharField(max_length=50, blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    long = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    location = models.PointField(blank=True, null=True)
    opening = models.TimeField(blank=True, null=True)
    closing = models.TimeField(blank=True, null=True)
    status = models.IntegerField(choices=SHOP_STATUS_CHOICES.choices(), blank=True, null=True)
    # delivery_type = MultiSelectField(choices=DELIVERY_CHOICES.choices())
    # self_delivery_charge = models.FloatField(blank=True, null=True)
    # delivery_radius = models.FloatField(blank=True, null=True)
    # bulk_delivery_charge = models.FloatField(blank=True, null=True)
    # within_km = models.FloatField(blank=True, null=True)
    # extra_charge_per_km = models.FloatField(blank=True, null=True)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
    logo = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
    rating = models.FloatField(default=5)
    available = models.BooleanField(default=True)
    vendor_id = models.CharField(max_length=30, blank=True, null=True)
    service_area = models.ForeignKey(ServiceArea, related_name='service_area_shops', on_delete=models.CASCADE,
                                      blank=True, null=True)

    def __str__(self):
        return self.shop_name


class Coupon(AuditedModel, models.Model):
    code = models.CharField(max_length=70, blank=True, null=True)
    discount = models.IntegerField(blank=True, null=True)
    is_percentage = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    shops = models.ManyToManyField(Shop, blank=True, null=True, related_name='shop_coupons')



class DeliveryOption(AuditedModel, models.Model):
    shop = models.ForeignKey(Shop, related_name='shop_delivery_options', on_delete=models.CASCADE)
    delivery_type = MultiSelectField(choices=DELIVERY_CHOICES.choices())
    delivery_charge = models.FloatField(blank=True, null=True)
    delivery_radius = models.FloatField(blank=True, null=True)
    free_delivery = models.BooleanField(default=False)
    free_delivery_for = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.shop.shop_name


class DeliveryVehicle(AuditedModel, models.Model):
    delivery_option = models.ForeignKey(DeliveryOption, related_name='delivery_option_vehicle',
                                        on_delete=models.CASCADE)
    vehicle_and_capacity = models.CharField(max_length=70, blank=True, null=True)
    min_charge = models.FloatField(blank=True, null=True)
    within_km = models.FloatField(blank=True, null=True)
    extra_charge_per_km = models.FloatField(blank=True, null=True)


class PaymentMethod(models.Model):
    payment_type = models.CharField(max_length=30, blank=True, null=True)
    choices = JSONField(default=dict(PAYMENT_CHOICES.choices()), blank=True, null=True)

    def __str__(self):
        return self.payment_type


class UserPaymentMethod(models.Model):
    user = models.ForeignKey(AppUser, related_name='user_payments', on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, related_name='user_payment_methods', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
