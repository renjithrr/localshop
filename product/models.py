from django.db import models
from utilities.utils import Kw, Konstants
from localshop.settings.storage_backends import PublicMediaStorage
from multiselectfield import MultiSelectField
from user.models import AuditedModel

CHOICES = Konstants(
    Kw(available=1, label='Available'),
    Kw(not_available=2, label='Not Available'),
)

UNIT_CHOICES = Konstants(
    Kw(number=1, label='Number'),
    Kw(kg=2, label='KG'),
    Kw(litre=3, label='Litre'),
)

COLOR_CHOICES = Konstants(
    Kw(v=1, label='Violet'),
    Kw(i=2, label='Indigo'),
    Kw(b=3, label='Blue'),
    Kw(g=4, label='Green'),
    Kw(y=5, label='Yellow'),
    Kw(o=6, label='Orange'),
    Kw(r=7, label='Red'),
)



class Brand(models.Model):
    name = models.CharField(max_length=255)
    status = models.IntegerField(choices=CHOICES.choices(), blank=True, null=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    status = models.IntegerField(choices=CHOICES.choices(), blank=True, null=True)

    def __str__(self):
        return self.name


class Product(AuditedModel, models.Model):
    name = models.CharField(max_length=255)
    product_id = models.CharField(max_length=10, blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    size = models.CharField(max_length=20, blank=True, null=True)
    color = MultiSelectField(choices=COLOR_CHOICES.choices())
    quantity = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    mrp = models.FloatField(max_length=100, blank=True, null=True)
    offer_prize = models.FloatField(max_length=100, blank=True, null=True)
    lowest_selling_rate = models.FloatField(max_length=100, blank=True, null=True)
    highest_selling_rate = models.FloatField(max_length=100, blank=True, null=True)
    hsn_code = models.CharField(max_length=10, blank=True, null=True)
    tax_rate = models.CharField(max_length=10, blank=True, null=True)
    moq = models.IntegerField(blank=True, null=True)
    unit = models.IntegerField(choices=UNIT_CHOICES.choices(), blank=True, null=True)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
    status = models.IntegerField(choices=CHOICES.choices(), blank=True, null=True, default=CHOICES.available)


    def __str__(self):
        return self.name


class ProductVarient(AuditedModel, models.Model):
    product = models.ForeignKey(Product, related_name='product_varients', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, choices=CHOICES.choices(), blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    color = MultiSelectField(choices=COLOR_CHOICES.choices())
    quantity = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    mrp = models.FloatField(max_length=100)
    offer_prize = models.FloatField(max_length=100, blank=True, null=True)
    lowest_selling_rate = models.FloatField(max_length=100, blank=True, null=True)
    highest_selling_rate = models.FloatField(max_length=100, blank=True, null=True)
    moq = models.IntegerField(blank=True, null=True)
    unit = models.IntegerField(choices=UNIT_CHOICES.choices(), blank=True, null=True)
    tax_rate = models.CharField(max_length=10, blank=True, null=True)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
    status = models.IntegerField(choices=CHOICES.choices(), blank=True, null=True, default=CHOICES.available)


class ProductVarientImage(models.Model):
    varient = models.ForeignKey(ProductVarient, on_delete=models.CASCADE)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)

# class Order(models.Model):
#     date = models.DateTimeField(auto_now_add=True)
#     sub_total = models.FloatField(max_length=100)
#     vat = models.FloatField(max_length=100)
#     total_amount = models.FloatField(max_length=100)
#     discount = models.FloatField(max_length=100)
#     grand_total = models.FloatField(max_length=100)
#     paid = models.FloatField(max_length=100)
#     due = models.FloatField(max_length=100)
#     payment_type = models.CharField(max_length=100)
#     payment_status = models.IntegerField()
#     status = models.IntegerField()
#
#
# class OrderItem(models.Model):
#     order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
#     product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
#
#     quantity = models.IntegerField()
#     rate = models.FloatField(max_length=100)
#     total = models.FloatField(max_length=100)
#     status = models.IntegerField()
