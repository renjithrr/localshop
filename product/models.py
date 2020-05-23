from django.db import models
from utilities.utils import Kw, Konstants
from localshop.settings.storage_backends import PublicMediaStorage


CHOICES = Konstants(
    Kw(available=1, label='Available'),
    Kw(not_available=2, label='Not Available'),
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



# class Brand(models.Model):
#     name = models.CharField(max_length=255)
#     status = models.CharField(max_length=10, choices=CHOICES.choices())
#
#     def __str__(self):
#         return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=CHOICES.choices())

    def __str__(self):
        return self.name


class Product(models.Model):
    # brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    size = models.CharField(max_length=10, choices=CHOICES.choices())
    color = models.CharField(max_length=10)
    code = models.CharField(max_length=10)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    mrp = models.FloatField(max_length=100)
    offer_prize = models.FloatField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=CHOICES.choices())
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


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
