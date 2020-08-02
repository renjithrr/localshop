from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
from django.db.models import Sum

from user.models import Shop, DeliveryOption
from product.models import Product, ProductVarientImage, ProductImage, ProductVarient
from customer.models import Address, ADDRESS_TYPES, Order, OrderItem


class DeliverySerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryOption
        fields = ['delivery_type', 'free_delivery', 'free_delivery_for']


class NearbyShopSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()
    delivery_methods = serializers.SerializerMethodField(source='shop.shop_name')

    class Meta:
        model = Shop
        fields = ['id', 'shop_name', 'address', 'business_name', 'distance', 'image', 'logo', 'lat', 'long', 'rating',
                  'delivery_methods']

    def get_distance(self, obj):
        location = self.context.get("location")
        round(obj.location.distance(location) * 100, 2)

    @staticmethod
    @swagger_serializer_method(serializer_or_field=DeliverySerializer(many=True))
    def get_delivery_methods(obj):
        delivery_options = obj.shop_delivery_options.all()
        return DeliverySerializer(delivery_options, many=True).data if delivery_options else []


class OrderSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product_id.name')
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

class CustomerOrderSerializer(serializers.ModelSerializer):
    shop = serializers.CharField(source='shop.shop_name')
    address = serializers.CharField(source='shop.address')
    orders = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['shop', 'address', 'created_at', 'grand_total', 'status', 'orders']

    @staticmethod
    @swagger_serializer_method(serializer_or_field=OrderSerializer(many=True))
    def get_orders(obj):
        orders = obj.order_items.all()
        return OrderSerializer(orders, many=True).data if orders else []


class CustomerAddressSerializer(serializers.ModelSerializer):
    address_type_label = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ['id', 'address', 'pincode', 'lat', 'long', 'locality', 'address_type', 'address_type_label']

    @staticmethod
    def get_address_type_label(obj):
        return ADDRESS_TYPES.get_label(obj.address_type)


class CustomerProductSerializer(serializers.ModelSerializer):
    # varients = serializers.SerializerMethodField('get_varients')
    product_images = serializers.SerializerMethodField('get_product_images')

    class Meta:
        model = Product
        fields = ['id', 'name', 'brand', 'size', 'color', 'quantity', 'mrp', 'offer_prize', 'lowest_selling_rate',
                  'highest_selling_rate', 'product_images']

    # def get_varients(self, obj):
    #     varients = obj.product_varients.all()
    #     return [{'name': obj.name, 'category': obj.category.id, 'size': varient.size, 'color':varient.color,
    #              'quantity':varient.quantity, 'description': varient.description, 'brand': varient.brand,
    #              'moq': varient.moq, 'offer_prize': varient.offer_prize,
    #              'lowest_selling_rate': varient.lowest_selling_rate, 'mrp': varient.mrp,
    #              'highest_selling_rate': varient.highest_selling_rate, 'hsn_code': obj.hsn_code,
    #              'tax_rate': varient.tax_rate, 'unit': varient.unit, 'id': varient.id,
    #              'images': [{'id': image.id, 'image_url': image.image.url}
    #               for image in ProductVarientImage.objects.filter(varient=varient)]} for varient in varients]

    def get_product_images(self, obj):
        return [{'id': image.id, 'image_url': image.image.url} for image in ProductImage.objects.filter(product=obj)]


class VarientSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = ProductVarient
        fields = ['product', 'size', 'color', 'brand', 'quantity', 'description', 'mrp', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'tax_rate', 'moq', 'unit', 'images']


    def get_images(self, obj):
        return [{'id': image.id, 'image_url': image.image.url}
                for image in ProductVarientImage.objects.filter(varient=obj)]


class OrderHistorySerializer(serializers.ModelSerializer):
    order_items = serializers.SerializerMethodField('get_order_items')
    total_amount = serializers.SerializerMethodField('get_total_amount')

    class Meta:
        model = Order
        fields = ['id', 'order_items', 'total_amount']

    def get_order_items(self, obj):
        return list(OrderItem.objects.filter(order_id=obj).values_list('product_id__name', flat=True))

    def get_total_amount(self, obj):
        return OrderItem.objects.filter(order_id=obj).aggregate(Sum('total'))['total__sum']
