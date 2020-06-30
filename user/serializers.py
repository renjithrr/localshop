from rest_framework import serializers
from user.models import AppUser as User, Shop, DeliveryOption, DeliveryVehicle


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['account_name', 'ifsc_code', 'account_number']


class ShopDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['user', 'vendor_name', 'shop_name', 'business_name', 'shop_category', 'gst_reg_number', 'opening',
                  'closing', 'fssai']


class ShopLocationDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['address', 'pincode', 'lat', 'long']


class DeliveryDetailSerializer(serializers.ModelSerializer):
    delivery_type = serializers.ListField()

    class Meta:
        model = DeliveryOption
        fields = ['delivery_type', 'delivery_charge', 'delivery_radius','shop']


class VehicleDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryVehicle
        fields = ['delivery_option', 'vehicle_and_capacity', 'min_charge','within_km', 'extra_charge_per_km']


class DeliveryRetrieveSerializer(serializers.ModelSerializer):
    vehicle_Details = serializers.SerializerMethodField('get_order_items')

    class Meta:
        model = DeliveryOption
        fields = ['delivery_type', 'delivery_charge', 'delivery_radius','shop', 'vehicle_Details']

    def get_order_items(self, obj):
        vehicles = obj.delivery_option_vehicle.all()
        return [{'vehicle_and_capacity': vehicle.vehicle_and_capacity, 'min_charge': vehicle.min_charge,
                 'within_km': vehicle.within_km, 'extra_charge_per_km': vehicle.extra_charge_per_km}
                for vehicle in vehicles]


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ['shop_name', 'gst_reg_number', 'opening', 'closing', 'image']
