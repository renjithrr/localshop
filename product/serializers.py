from rest_framework import serializers
from product.models import Product, ProductVarient


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'category', 'size', 'color', 'quantity', 'description', 'brand']


class ProductPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['mrp', 'offer_prize', 'lowest_selling_rate', 'highest_selling_rate', 'hsn_code', 'tax_rate', 'moq']


class ProductListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description']


class ProductVarientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVarient
        fields = ['product', 'size', 'color', 'brand', 'quantity', 'description', 'mrp', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'tax_rate', 'moq', 'unit']

