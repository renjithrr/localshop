from django.contrib.gis.db import models
from user.models import AuditedModel, AppUser, PAYMENT_CHOICES, Shop, DELIVERY_CHOICES
from utilities.utils import Kw, Konstants
from product.models import Product


ADDRESS_TYPES = Konstants(
    Kw(home=1, label='Home'),
    Kw(work=2, label='Work'),
    Kw(other=3, label='Other'),
)


ORDER_STATUS = Konstants(
    Kw(pending=1, label='Pending'),
    Kw(accepted=2, label='Accepted'),
    Kw(rejected=3, label='Rejected'),
    Kw(picked_up=4, label='Order has picked up'),
    Kw(delivered=5, label='Delivered'),
)


PAYMENT_STATUS = Konstants(
    Kw(pending=1, label='Pending'),
    Kw(completed=2, label='Completed'),
    Kw(failed=3, label='Failed'),
)


class Customer(models.Model):
    user = models.OneToOneField(AppUser, related_name='customer', on_delete=models.CASCADE)
    bargain_count = models.IntegerField(default=0)
    bargain_upto = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username


class Address(AuditedModel, models.Model):
    customer = models.ForeignKey(Customer, related_name='customer_addresses', on_delete=models.CASCADE, blank=True,
                                 null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    lat = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    long = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    location = models.PointField(blank=True, null=True)
    locality = models.CharField(max_length=30, blank=True, null=True)
    address_type = models.IntegerField(choices=ADDRESS_TYPES.choices(), default=ADDRESS_TYPES.home)
    is_deleted = models.BooleanField(default=False)


class Order(AuditedModel, models.Model):
    sub_total = models.FloatField(max_length=100, blank=True, null=True)
    vat = models.FloatField(max_length=100, blank=True, null=True)
    total_amount = models.FloatField(max_length=100, blank=True, null=True)
    discount = models.FloatField(max_length=100, blank=True, null=True)
    grand_total = models.FloatField(max_length=100, blank=True, null=True)
    paid = models.FloatField(max_length=100, blank=True, null=True)
    due = models.FloatField(max_length=100, blank=True, null=True)
    payment_type = models.IntegerField(choices=PAYMENT_CHOICES.choices(), blank=True, null=True)
    payment_status = models.IntegerField(choices=PAYMENT_STATUS.choices(), blank=True, null=True)
    status = models.IntegerField(choices=ORDER_STATUS.choices(), blank=True, null=True)
    shop = models.ForeignKey(Shop, related_name='shop_orders', on_delete=models.CASCADE, blank=True, null=True)
    customer = models.ForeignKey(Customer, related_name='customer_orders', on_delete=models.CASCADE,
                                 blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    customer_otp = models.CharField(max_length=6, blank=True, null=True)
    rating = models.FloatField(default=5)
    payment_message = models.TextField(blank=True, null=True)
    cod = models.BooleanField(default=True)
    delivery_type = models.IntegerField(choices=DELIVERY_CHOICES.choices(), blank=True, null=True)

    def __str__(self):
        return str(self.id)


class OrderItem(AuditedModel, models.Model):
    order_id = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.IntegerField(blank=True, null=True)
    rate = models.FloatField(max_length=100, blank=True, null=True)
    total = models.FloatField(max_length=100, blank=True, null=True)
    # status = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return str(self.product_id)


class CustomerFavouriteProduct(AuditedModel, models.Model):
    product = models.ForeignKey(Product, related_name='product_favourites', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name='customer_favoutites', on_delete=models.CASCADE)
