from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
from django.db.models import Sum

from user.models import Shop, DeliveryOption, DELIVERY_CHOICES
from product.models import Product, ProductVarientImage, ProductImage, ProductVarient,  Category
from customer.models import Address, ADDRESS_TYPES, Order, OrderItem


#
# class DeliverySerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = DeliveryOption
#         fields = ['delivery_type', 'free_delivery', 'free_delivery_for']


class NearbyShopSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()
    # delivery_methods = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    pick_up = serializers.SerializerMethodField()
    home_delivery = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['id', 'shop_name', 'address', 'business_name', 'distance', 'image', 'logo', 'lat', 'long', 'rating'
            , 'category', 'pick_up', 'home_delivery']

    def get_distance(self, obj):
        location = self.context.get("location")
        return round(obj.location.distance(location) * 100, 2)

    def get_category(self, obj):
        return {'id': obj.shop_category.id, 'name': obj.shop_category.name}

    def get_pick_up(self, obj):
        pickup = obj.shop_delivery_options.all()
        pick_up = False
        for value in pickup:
            for data in value.delivery_type:
                if int(data) == DELIVERY_CHOICES.pickup:
                    pick_up = True
                    break

        return pick_up
        # for i in obj.shop_delivery_options.all():
        #     d = i.delivery_type
        #     for j in d:
        #         print(
        #             j
        #         )
        # return True if pickup else False

    def get_home_delivery(self, obj):
        pickup = obj.shop_delivery_options.all()
        pick_up = False
        for value in pickup:
            for data in value.delivery_type:
                if int(data) == DELIVERY_CHOICES.shop_ship:
                    pick_up = True
                    break

        return pick_up

    # @staticmethod
    # @swagger_serializer_method(serializer_or_field=DeliverySerializer(many=True))
    # def get_delivery_methods(obj):
    #     delivery_options = obj.shop_delivery_options.all()
    #     return DeliverySerializer(delivery_options, many=True).data if delivery_options else []


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
    products = serializers.SerializerMethodField('get_products')
    class Meta:
        model = Category
        fields = ['name', 'products']
    # product_images = serializers.SerializerMethodField('get_product_images')

        # class Meta:
        #     model = Product
        # fields = ['id', 'name', 'brand', 'size', 'color', 'quantity', 'mrp', 'offer_prize', 'lowest_selling_rate',
        #           'highest_selling_rate', 'product_images', 'shop', 'rating', 'description', 'is_favourite', 'moq']

    def get_products(self, obj):
        shop = self.context.get('shop')
        products = Product.objects.filter(shop=shop, category=obj)
        search = self.context.get('search')
        if search:
            products = products.filter(name__icontains=search)
        return [{'name': product.name, 'brand': product.brand, 'size': product.size, 'quantity':product.quantity,
                 'mrp':product.mrp, 'lowest_selling_rate': product.lowest_selling_rate,
                 'moq': product.moq, 'offer_prize': product.offer_prize,
                 'highest_selling_rate': product.highest_selling_rate, 'rating': product.rating,
                 'shop': product.shop.id, 'hsn_code': product.hsn_code,
                 'description': product.description, 'is_favourite': product.is_favourite,
                 'id': product.id, 'color': product.color, 'is_best_Seller': product.is_best_Seller,
                 'is_bargain_possible': product.is_bargain_possible, 'offer_percentage': product.offer_percentage,
                 'product_images': [{'id': image.id, 'image_url': image.image.url}
                  for image in ProductImage.objects.filter(product=product)]} for product in products]

    # def get_product_images(self, obj):
    #     return [{'id': image.id, 'image_url': image.image.url} for image in ProductImage.objects.filter(product=obj)]


class VarientSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProductVarient
        fields = ['product', 'size', 'color', 'brand', 'quantity', 'description', 'mrp', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'tax_rate', 'moq', 'unit', 'images', 'rating',
                  'is_favourite', 'name', 'id']

    def get_name(self, obj):
        return obj.product.name


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
