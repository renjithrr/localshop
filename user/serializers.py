from rest_framework import serializers
from user.models import AppUser as User, Shop


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['account_name', 'ifsc_code', 'account_number']


class ShopDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['user', 'vendor_name', 'shop_name', 'business_name', 'shop_category', 'gst_reg_number']


class ShopLocationDataSerializer(serializers.ModelSerializer):
    delivery_type = serializers.ListField()
    class Meta:
        model = Shop
        fields = ['address', 'pincode', 'lat', 'long', 'opening', 'closing', 'delivery_type']
