from rest_framework import serializers
from product.models import Product, ProductVarient


class ProductSerializer(serializers.ModelSerializer):
    color = serializers.ListField()
    class Meta:
        model = Product
        fields = ['name', 'category', 'size', 'color', 'quantity', 'description', 'brand', 'product_id', 'mrp',
                  'offer_prize', 'lowest_selling_rate', 'highest_selling_rate',
                  'hsn_code', 'tax_rate', 'moq', 'unit']


class ProductPricingSerializer(serializers.ModelSerializer):
    product_id = serializers.SerializerMethodField('get_id')
    class Meta:
        model = Product
        fields = ['product_id', 'mrp', 'offer_prize', 'lowest_selling_rate', 'highest_selling_rate',
                  'hsn_code', 'tax_rate', 'moq', 'unit']

    def get_id(self, obj):
        return obj.id


class ProductListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description']


class ProductVarientSerializer(serializers.ModelSerializer):
    color = serializers.ListField()
    class Meta:
        model = ProductVarient
        fields = ['product', 'size', 'color', 'brand', 'quantity', 'description', 'mrp', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'tax_rate', 'moq', 'unit']

