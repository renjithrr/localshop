from rest_framework import serializers
from user.models import Shop
from product.models import Order
from customer.models import Address, ADDRESS_TYPES


class NearbyShopSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['shop_name', 'address', 'business_name', 'distance', 'image', 'logo']

    def get_distance(self, obj):
        location = self.context.get("location")
        round(obj.location.distance(location) * 100, 2)


class CustomerOrderSerializer(serializers.ModelSerializer):
    shop = serializers.SerializerMethodField(source='shop.shop_name')
    address = serializers.SerializerMethodField(source='shop.address')
    orders = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['shop', 'address', 'created_at', 'grand_total', 'status', 'orders']

    @staticmethod
    def get_orders(obj):
        return [{'product': item.product_id.name, 'quantity': item.quantity}
                for item in obj.order_items.all()]



class CustomerAddressSerializer(serializers.ModelSerializer):
    address_type_label = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ['id', 'address', 'pincode', 'lat', 'long', 'locality', 'address_type', 'address_type_label']

    @staticmethod
    def get_address_type_label(obj):
        return ADDRESS_TYPES.get_label(obj.address_type)
