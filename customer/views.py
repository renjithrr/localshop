from django.contrib.gis.measure import D
from django.contrib.gis.geos import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework. viewsets import GenericViewSet
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from user.models import Shop
from customer.serializers import NearbyShopSerializer, CustomerOrderSerializer, CustomerAddressSerializer
from utilities.mixins import ResponseViewMixin
from utilities.messages import SUCCESS, GENERAL_ERROR
from user.models import ShopCategory, PaymentMethod
from customer.models import Customer, Address


class NearbyShop(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    latitude = openapi.Parameter('search', openapi.IN_QUERY, description="search product by key",
                                   type=openapi.TYPE_STRING)
    longitude = openapi.Parameter('all', openapi.IN_QUERY, description="List all products",
                                    type=openapi.TYPE_STRING)
    shop_category = openapi.Parameter('all', openapi.IN_QUERY, description="List all products",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[latitude, longitude, shop_category])
    def get(self, request):
        try:

            latitude = request.GET.get('latitude', 0)
            longitude = request.GET.get('longitude', 0)
            location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
            query_set = Shop.objects.filter(location__distance_lte=(location, D(km=5)))
            if request.GET.get('shop_category', ''):
                query_set = query_set.filter(shop_category=request.GET.get('shop_category', ''))
            serializer = NearbyShopSerializer(query_set, context={'location': location}, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'shops': serializer.data},
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class CommonParamsView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            shop_choices = [{'id': shop.id, 'category': shop.name}
                            for shop in ShopCategory.objects.all()]
            payment_methods = [{'id': method.id, 'method': method.payment_type}
                               for method in PaymentMethod.objects.all()]
            return self.success_response(code='HTTP_200_OK',
                                         data={'shopcategories': shop_choices,
                                               'payment_methods': payment_methods
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class OrderHistoryView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    customer = openapi.Parameter('customer_id', openapi.IN_QUERY, description="Customer ID",
                                 type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['customer'], manual_parameters=[customer])
    def get(self, request):
        try:
            customer = Customer.objects.get(id=request.GET.get('customer_id'))
            orders = customer.customer_orders
            serializer = CustomerOrderSerializer(orders, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'orders': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class CustomerAddressView(GenericViewSet, ResponseViewMixin):
    permission_classes = [AllowAny]
    serializer_class = CustomerAddressSerializer
    customer = openapi.Parameter('customer_id', openapi.IN_QUERY, description="Customer ID",
                                 type=openapi.TYPE_STRING)

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['product'], request_body=CustomerAddressSerializer)
    def create(self, request):
        try:
            address = Address.objects.get(id=request.data.get('id'))
            serializer = CustomerAddressSerializer(instance=address, data=request.data)
        except Address.DoesNotExist:
            serializer = CustomerAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        else:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    @swagger_auto_schema(tags=['product'], manual_parameters=[customer])
    def list(self, request, *args, **kwargs):
        try:
            adresses = Address.objects.filter(customer=request.GET.get('customer', ''))
            serializer = CustomerAddressSerializer(adresses, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))

    def retrieve(self, request, pk=None):
        try:
            address = Address.objects.get(id=pk)
            serializer = CustomerAddressSerializer(address)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Address.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
