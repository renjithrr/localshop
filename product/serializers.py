from rest_framework import serializers
from product.models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'category', 'image', 'size', 'color', 'quantity', 'mrp', 'offer_prize', 'description']
