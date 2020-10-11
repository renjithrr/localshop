
from rest_framework import serializers
from datetime import datetime, timezone

from customer.models import Order,OrderItem
from user.models import Shop, DeliveryOption, UserPaymentMethod
from product.models import Product

class AdminOrderSerializer(serializers.ModelSerializer):
    delay = serializers.SerializerMethodField()


    class Meta:
        model = Order
        fields = ['id', 'delay', 'status']

    @staticmethod
    def get_delay(obj):
        created_time = obj.created_at
        current_time = datetime.now((timezone.utc))
        difference = current_time - created_time
        return str(int(difference.seconds / 60)) + " min"



class OrderDetailsSerializer(serializers.ModelSerializer):
    delay = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    shop_details = serializers.SerializerMethodField()
    customer_details = serializers.SerializerMethodField()
    delivery_boy_details = serializers.SerializerMethodField()


    class Meta:
        model = Order
        fields = ['id', 'delay', 'status', 'items', 'payment_type','shop_details', 'customer_details','delivery_boy_details']

    @staticmethod
    def get_delay(self):
        created_time = self.created_at
        current_time = datetime.now((timezone.utc))
        difference = current_time - created_time
        return str(int(difference.seconds / 60)) + " min"

    def get_items(self,obj):
        items = OrderItem.objects.filter(order_id=obj.id)
        items_list = []
        for item in items:
            item_dict = {"item": item.product_id.name, "quantity": item.quantity, "price": item.rate, "total": item.total}
            dictionary_copy = item_dict.copy()
            items_list.append(dictionary_copy)
        return items_list

    def get_shop_details(self,obj):
        return {"shop_name": obj.shop.shop_name, "phone_number": obj.shop.user.mobile_number, 'address': obj.shop.address}

    def get_customer_details(self,obj):
        return {"customer_name":obj.customer.user.account_name, "phone_number": obj.customer.user.mobile_number,"address":"test"}

    def get_delivery_boy_details(self,obj):
        return  {"name":"sanooj","phone_number":"9048799685"}


class AdminShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['shop_name', 'vendor_name', 'logo', 'id']


class ShopDetailsSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    delivery_type = serializers.SerializerMethodField()
    account_number = serializers.SerializerMethodField()
    ifsc_code = serializers.SerializerMethodField()
    payment_methods = serializers.SerializerMethodField()
    shop_category_name = serializers.SerializerMethodField()
    shop_category_description = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['shop_name', 'phone_number', 'address', 'vendor_name', 'shop_category_name', 'shop_category_description', 'lat', 'long', 'pincode', 'gst_reg_number', 'delivery_type', 'account_number', 'ifsc_code', 'payment_methods','gst_image']

    @staticmethod
    def get_phone_number(self):
        return self.user.mobile_number

    def get_delivery_type(self, obj):
        try:
            delivery = DeliveryOption.objects.get(shop=obj.id)
        except DeliveryOption.DoesNotExist:
            return ""
        return delivery.delivery_type

    def get_account_number(self, obj):
        return obj.user.account_number

    def shop_category(self, obj):
        return obj.shop_category.name

    def get_shop_category_name(self, obj):
        return obj.shop_category.name

    def get_shop_category_description(self, obj):
        return obj.shop_category.description

    def get_ifsc_code(self,obj):
        return obj.user.ifsc_code

    def get_payment_methods(self,obj):
        try:
            payments = UserPaymentMethod.objects.get(user=obj.user)
        except UserPaymentMethod.DoesNotExist:
            return ""
        return payments


class ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'category', 'size', 'color', 'quantity', 'description', 'brand', 'mrp', 'offer_prize', 'lowest_selling_rate', 'highest_selling_rate', 'hsn_code', 'tax_rate', 'moq', 'unit']
