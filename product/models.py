from django.db import models
from utilities.utils import Kw, Konstants
from localshop.settings.storage_backends import PublicMediaStorage
from user.models import AuditedModel, PAYMENT_CHOICES, Shop
from customer.models import Customer

CHOICES = Konstants(
    Kw(available=1, label='Available'),
    Kw(not_available=2, label='Not Available'),
)

UNIT_CHOICES = Konstants(
    Kw(number='number', label='Number'),
    Kw(kg='kg', label='KG'),
    Kw(litre='litre', label='Litre'),
)

ORDER_STATUS = Konstants(
    Kw(pending=1, label='Pending'),
    Kw(accepted=2, label='Accepted'),
    Kw(rejected=3, label='Rejected'),
    Kw(ready_for_pickup=4, label='Ready for pickup'),
    Kw(delivered=5, label='Delivered'),
)


PAYMENT_STATUS = Konstants(
    Kw(pending=1, label='Pending'),
    Kw(completed=2, label='Completed'),
    Kw(failed=3, label='Failed'),
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
    product_id = models.CharField(max_length=15, blank=True, null=True)
    brand = models.CharField(max_length=30, blank=True, null=True)
    # brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    size = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    mrp = models.FloatField(max_length=100, blank=True, null=True)
    offer_prize = models.FloatField(max_length=100, blank=True, null=True)
    lowest_selling_rate = models.FloatField(max_length=100, blank=True, null=True)
    highest_selling_rate = models.FloatField(max_length=100, blank=True, null=True)
    hsn_code = models.CharField(max_length=10, blank=True, null=True)
    tax_rate = models.CharField(max_length=10, blank=True, null=True)
    moq = models.IntegerField(blank=True, null=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES.choices(), blank=True, null=True)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
    status = models.IntegerField(choices=CHOICES.choices(), blank=True, null=True, default=CHOICES.available)
    is_deleted = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    shop = models.ManyToManyField(Shop, related_name='shop_products', blank=True, null=True)


    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='product_images', on_delete=models.CASCADE, blank=True, null=True)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)


class ProductVarient(AuditedModel, models.Model):
    product = models.ForeignKey(Product, related_name='product_varients', on_delete=models.CASCADE)
    size = models.CharField(max_length=20, blank=True, null=True)
    brand = models.CharField(max_length=30, blank=True, null=True)
    # brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    mrp = models.FloatField(max_length=100)
    offer_prize = models.FloatField(max_length=100, blank=True, null=True)
    lowest_selling_rate = models.FloatField(max_length=100, blank=True, null=True)
    highest_selling_rate = models.FloatField(max_length=100, blank=True, null=True)
    moq = models.IntegerField(blank=True, null=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES.choices(), blank=True, null=True)
    tax_rate = models.CharField(max_length=10, blank=True, null=True)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)
    status = models.IntegerField(choices=CHOICES.choices(), blank=True, null=True, default=CHOICES.available)
    is_deleted = models.BooleanField(default=False)
    is_hidden= models.BooleanField(default=False)



class ProductVarientImage(models.Model):
    varient = models.ForeignKey(ProductVarient, on_delete=models.CASCADE, blank=True, null=True)
    image = models.ImageField(storage=PublicMediaStorage(), blank=True, null=True)


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
