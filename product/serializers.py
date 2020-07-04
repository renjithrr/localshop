from rest_framework import serializers
from product.models import Product, ProductVarient, Order, OrderItem
from django.db.models import Sum


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'category', 'size', 'color', 'quantity', 'description', 'brand', 'product_id']


class ProductRetrieveSerializer(serializers.ModelSerializer):
    varients = serializers.SerializerMethodField('get_varients')

    class Meta:
        model = Product
        fields = ['name', 'category', 'size', 'color', 'quantity', 'description', 'brand', 'moq', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'hsn_code', 'tax_rate', 'moq', 'unit', 'varients']

    def get_varients(self, obj):
        varients = obj.product_varients.all()
        return [{'name': obj.name, 'category': obj.category.id, 'size': varient.size, 'color':varient.color,
                 'quantity':varient.quantity, 'description': varient.description, 'brand': varient.brand,
                 'moq': varient.moq, 'offer_prize': varient.offer_prize,
                 'lowest_selling_rate': varient.lowest_selling_rate,
                 'highest_selling_rate': varient.highest_selling_rate, 'hsn_code': obj.hsn_code,
                 'tax_rate': varient.tax_rate, 'unit': varient.unit, 'id': varient.id} for varient in varients]


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
    class Meta:
        model = ProductVarient
        fields = ['product', 'size', 'color', 'brand', 'quantity', 'description', 'mrp', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'tax_rate', 'moq', 'unit']


class ProductUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['size', 'color', 'brand', 'quantity', 'description', 'mrp', 'offer_prize',
                  'lowest_selling_rate', 'highest_selling_rate', 'tax_rate', 'moq', 'unit']


class OrderSerializer(serializers.ModelSerializer):
    order_items = serializers.SerializerMethodField('get_order_items')
    total_amount = serializers.SerializerMethodField('get_total_amount')

    class Meta:
        model = Order
        fields = ['id', 'order_items', 'total_amount']

    def get_order_items(self, obj):
        return list(OrderItem.objects.filter(order_id=obj).values_list('product_id__name', flat=True))

    def get_total_amount(self, obj):
        return OrderItem.objects.filter(order_id=obj).aggregate(Sum('total'))['total__sum']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField('get_items')

    class Meta:
        model = Order
        fields = ['id', 'items']

    def get_items(self, obj):
        return [{'name': item.product_id.name, 'category': item.product_id.category.name, 'size': item.product_id.size,
                 'color': item.product_id.color, 'quantity': item.quantity, 'total': item.total,
                 'description': item.product_id.description, 'brand': item.product_id.brand,
                 'product_id': item.product_id.product_id}
                for item in OrderItem.objects.filter(order_id=obj)]
