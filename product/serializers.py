from rest_framework import serializers
from product.models import Product, ProductVarient, Order, OrderItem


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
        fields = ['id', 'product_id', 'brand', 'name', 'quantity', 'mrp']


class ProductVarientSerializer(serializers.ModelSerializer):
    color = serializers.ListField()
    class Meta:
        model = ProductVarient
        fields = ['product', 'size', 'color', 'brand', 'quantity', 'description', 'mrp', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'tax_rate', 'moq', 'unit']


class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField('get_product_name')

    class Meta:
        model = OrderItem
        fields = ['order_id', 'product_name', 'quantity', 'total']

    def get_product_name(self, obj):
        return obj.product_id.name
