from datetime import datetime
from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
from django.db.models import Sum

from user.models import Shop, DeliveryOption, DELIVERY_CHOICES, ServiceArea
from product.models import Product, ProductVarientImage, ProductImage, ProductVarient,  Category
from product.serializers import ProductListingSerializer
from customer.models import Address, ADDRESS_TYPES, Order, OrderItem, Customer, ORDER_STATUS, PAYMENT_CHOICES,\
    CustomerFavouriteProduct


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
    shop_available = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['id', 'shop_name', 'address', 'business_name', 'distance', 'image', 'logo', 'lat', 'long', 'rating'
            , 'category', 'pick_up', 'home_delivery', 'shop_available']

    def get_distance(self, obj):
        location = self.context.get("location")
        if location:
            return round(obj.location.distance(location) * 100, 2)
        return ''

    @staticmethod
    def get_shop_available(obj):
        return obj.available

    def get_category(self, obj):
        return {'id': obj.shop_category.id, 'name': obj.shop_category.name, 'card_type': obj.shop_category.card_type}

    def get_pick_up(self, obj):
        delivery_option = obj.shop_delivery_options.all().last()
        pick_up = False
        for value in delivery_option.delivery_type:
            if int(value) == DELIVERY_CHOICES.pickup:
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
        delivery_option = obj.shop_delivery_options.all().last()
        pick_up = False
        for value in delivery_option.delivery_type:
            if int(value) == DELIVERY_CHOICES.bulk_delivery or int(value) == DELIVERY_CHOICES.self_delivery \
                    or int(value) == DELIVERY_CHOICES.townie_ship:
                pick_up = True
                break

        return pick_up

    # @staticmethod
    # @swagger_serializer_method(serializer_or_field=DeliverySerializer(many=True))
    # def get_delivery_methods(obj):
    #     delivery_options = obj.shop_delivery_options.all()
    #     return DeliverySerializer(delivery_options, many=True).data if delivery_options else []

class ShopOrderSerializer(serializers.ModelSerializer):
    mobile_number = serializers.CharField(source='user.mobile_number')
    shop_available = serializers.SerializerMethodField()
    class Meta:
        model = Shop
        fields = ['shop_name', 'business_name', 'address', 'mobile_number', 'lat', 'long', 'shop_available']

    @staticmethod
    def get_shop_available(obj):
        if obj.opening < datetime.now().time() < obj.closing:
            return True
        else:
            return False


class OrderSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product_id.name')
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'rate']


class OrderCustomerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.first_name')
    mobile_number = serializers.CharField(source='user.mobile_number')
    address_details = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['name', 'mobile_number', 'address_details']

    @staticmethod
    def get_address_details(obj):
        address = obj.customer_addresses.filter(is_deleted=False).last()
        return [{'address': address.address, 'lat': address.lat, 'long': address.long}] if address else []


class CustomerOrderSerializer(serializers.ModelSerializer):
    shop = serializers.SerializerMethodField()
    order_items = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    payment_type_label = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'shop', 'created_at', 'grand_total', 'status','status_label', 'order_items','status',
                  'customer', 'payment_type', 'payment_type_label', 'grand_total', 'cod']

    @staticmethod
    @swagger_serializer_method(serializer_or_field=OrderSerializer(many=True))
    def get_order_items(obj):
        orders = obj.order_items.all()
        return OrderSerializer(orders, many=True).data if orders else []

    @staticmethod
    def get_shop(obj):
        return ShopOrderSerializer(obj.shop).data

    @staticmethod
    def get_customer(obj):
        return OrderCustomerSerializer(obj.customer).data

    @staticmethod
    def get_status_label(obj):
        return ORDER_STATUS.get_label(obj.status)

    @staticmethod
    def get_payment_type_label(obj):
        return PAYMENT_CHOICES.get_label(obj.payment_type)


class CustomerAddressSerializer(serializers.ModelSerializer):
    address_type_label = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ['id', 'address', 'pincode', 'lat', 'long', 'locality', 'address_type', 'address_type_label']

    @staticmethod
    def get_address_type_label(obj):
        return ADDRESS_TYPES.get_label(obj.address_type)


class ProductListSerializer(serializers.ModelSerializer):
    product_images = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id','name', 'category', 'size', 'color', 'quantity', 'description', 'brand', 'product_id', 'mrp',
                  'offer_prize', 'hsn_code', 'moq', 'tax_rate', 'unit', 'lowest_selling_rate', 'highest_selling_rate',
                  'is_best_Seller', 'is_bargain_possible', 'offer_percentage', 'product_images', 'is_favourite']

    def get_product_images(self, obj):
        return [{'id': image.id, 'image_url': image.image.url}
         for image in ProductImage.objects.filter(product=obj)]

    def get_is_favourite(self, obj):
        # print(self.context)
        if self.context:
            # print(self.context.get('user'), "aaaaaaaa")
            return True if CustomerFavouriteProduct.objects.filter(product=obj,
                                                       customer=Customer.objects.get(user=self.context))\
                else obj.is_favourite
        return False

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
        # # print(self.context.get('user'), "Dddddddd")
        if search:
            products = products.filter(name__icontains=search)
        return ProductListSerializer(products, context=self.context.get('user'), many=True).data
        # return [{'name': product.name, 'brand': product.brand, 'size': product.size, 'quantity':product.quantity,
        #          'mrp':product.mrp, 'lowest_selling_rate': product.lowest_selling_rate,
        #          'moq': product.moq, 'offer_prize': product.offer_prize,
        #          'highest_selling_rate': product.highest_selling_rate, 'rating': product.rating,
        #          'shop': product.shop.id, 'hsn_code': product.hsn_code,
        #          'description': product.description,
        #          'is_favourite': True if self.context.get('user') and CustomerFavouriteProduct.objects.
        #              filter(product=product, customer=Customer.objects.get(user=self.context.get('user'))) else product.is_favourite,
        #          'id': product.id, 'color': product.color, 'is_best_Seller': product.is_best_Seller,
        #          'is_bargain_possible': product.is_bargain_possible, 'offer_percentage': product.offer_percentage,
        #          'product_images': [{'id': image.id, 'image_url': image.image.url}
        #           for image in ProductImage.objects.filter(product=product)]} for product in products]

    # def get_product_images(self, obj):
    #     return [{'id': image.id, 'image_url': image.image.url} for image in ProductImage.objects.filter(product=obj)]


class VarientSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProductVarient
        fields = ['product', 'size', 'color', 'brand', 'quantity', 'description', 'mrp', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'tax_rate', 'moq', 'unit', 'images', 'rating',
                  'is_favourite', 'name', 'id', 'is_bargain_possible']

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
        fields = ['id', 'order_items', 'total_amount', 'otp']

    def get_order_items(self, obj):
        return list(OrderItem.objects.filter(order_id=obj).values_list('product_id__name', flat=True))

    def get_total_amount(self, obj):
        return OrderItem.objects.filter(order_id=obj).aggregate(Sum('total'))['total__sum']


class CustomerShopSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    pick_up = serializers.SerializerMethodField()
    home_delivery = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['id', 'shop_name', 'address', 'business_name', 'image', 'logo', 'lat', 'long', 'rating'
            , 'category', 'pick_up', 'home_delivery', 'products']

    def get_image(self, obj):
        return obj.image.url if obj.image else ''

    def get_category(self, obj):
        return {'id': obj.shop_category.id, 'name': obj.shop_category.name, 'card_type': obj.shop_category.card_type}

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
                if int(data) == DELIVERY_CHOICES.pickup:
                    pick_up = True
                    break

        return pick_up

    def get_products(self, obj):
        # print(self.context)
        categories = Category.objects.filter(product__isnull=False, product__shop=obj)
        product_serializer = CustomerProductSerializer(categories, context={'shop': obj, 'user': self.context['user']},
                                                       many=True)
        return product_serializer.data



class ShopBannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['id', 'shop_name', 'image']

    def get_image(self, obj):
        return obj.image.url if obj.image else ''


class CustomerOrderHistorySerializer(serializers.ModelSerializer):
    shop = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    shop_available = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['shop', 'products', 'grand_total', 'created_at', 'rating', 'customer_otp', 'id', 'status',
                  'status_label', 'shop_available']

    @staticmethod
    def get_shop(obj):
        return NearbyShopSerializer(obj.shop).data
        # return [{'id': obj.shop.id, 'name': obj.shop.shop_name, 'lat': obj.shop.lat, 'long': obj.shop.long,
        #          'rating': obj.shop.rating, 'address': obj.shop.address, 'shop_available': obj.shop.available}]

    @staticmethod
    def get_shop_available(obj):
        if obj.opening < datetime.now().time() < obj.closing:
            return True
        else:
            return False

    @staticmethod
    def get_status_label(obj):
        return ORDER_STATUS.get_label(obj.status)

    @staticmethod
    def get_products(obj):
        products = obj.order_items.all()
        print(products)
        return [{'name': product.product_id.name, 'brand': product.product_id.brand,
                                    'size': product.product_id.size,
                 'quantity': product.quantity, 'mrp': product.product_id.mrp,
                 'lowest_selling_rate': product.product_id.lowest_selling_rate,
                 'moq': product.product_id.moq, 'offer_prize': product.product_id.offer_prize,
                 'highest_selling_rate': product.product_id.highest_selling_rate, 'rating': product.rating,
                 'shop': obj.shop.id if obj.shop else '', 'hsn_code': product.product_id.hsn_code,
                 'description': product.product_id.description, 'is_favourite': product.product_id.is_favourite,
                 'id': product.product_id.id, 'color': product.product_id.color,
                 'is_best_Seller': product.product_id.is_best_Seller,
                 'is_bargain_possible': product.product_id.is_bargain_possible,
                 'offer_percentage': product.product_id.offer_percentage, 'category': product.product_id.category.name,
                 'product_images': [{'id': image.id if image else '', 'image_url': image.image.url if image else ''}
                                    for image in ProductImage.objects.filter(product=product.product_id)]} for product in products]


class CustomerProductSearchSerializer(serializers.ModelSerializer):
    product_images = serializers.SerializerMethodField('get_product_images')
    shop_details = serializers.SerializerMethodField()
    # shop_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'brand', 'size', 'quantity', 'mrp', 'lowest_selling_rate', 'moq', 'offer_prize',
                  'highest_selling_rate', 'rating', 'shop_details', 'hsn_code', 'description', 'is_favourite', 'color',
                  'is_best_Seller', 'is_bargain_possible', 'offer_percentage', 'product_images']
    # product_images = serializers.SerializerMethodField('get_product_images')

        # class Meta:
        #     model = Product
        # fields = ['id', 'name', 'brand', 'size', 'color', 'quantity', 'mrp', 'offer_prize', 'lowest_selling_rate',
        #           'highest_selling_rate', 'product_images', 'shop', 'rating', 'description', 'is_favourite', 'moq']

    def get_product_images(self, obj):
        return [{'id': image.id if image else '', 'image_url': image.image.url if image else ''}
         for image in ProductImage.objects.filter(product=obj)]

    def get_shop_details(self, obj):
        return NearbyShopSerializer(obj.shop).data




class ServiceAreaSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceArea
        fields = ['id', 'name', 'lat', 'long']
