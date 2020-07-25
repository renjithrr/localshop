from django.contrib.gis.measure import D
from django.contrib.gis.geos import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework. viewsets import GenericViewSet
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from user.models import Shop
from customer.serializers import NearbyShopSerializer, CustomerOrderSerializer, CustomerAddressSerializer,\
    ProductSerializer
from utilities.mixins import ResponseViewMixin
from utilities.messages import SUCCESS, GENERAL_ERROR
from utilities.utils import deliver_sms, OTPgenerator
from user.models import ShopCategory, PaymentMethod, USER_TYPE_CHOICES, AppUser
from customer.models import Customer, Address, CustomerFavouriteProduct


class NearbyShop(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    latitude = openapi.Parameter('search', openapi.IN_QUERY, description="latitude",
                                   type=openapi.TYPE_STRING)
    longitude = openapi.Parameter('all', openapi.IN_QUERY, description="longitude",
                                    type=openapi.TYPE_STRING)
    shop_category = openapi.Parameter('shop_category', openapi.IN_QUERY, description="List all products",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[latitude, longitude, shop_category],
                         responses={'500': GENERAL_ERROR, '200': NearbyShopSerializer})
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
    permission_classes = [IsAuthenticated]

    token = openapi.Parameter('customer_id', openapi.IN_QUERY, description="Pass token in headers",
                                 type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['customer'], manual_parameters=[token],
                         responses={'500': GENERAL_ERROR, '200': CustomerOrderSerializer})
    def get(self, request):
        try:
            customer = Customer.objects.get(user=request.user)
            orders = customer.customer_orders
            serializer = CustomerOrderSerializer(orders, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'orders': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class CustomerAddressView(GenericViewSet, ResponseViewMixin):
    permission_classes = [AllowAny]
    serializer_class = CustomerAddressSerializer
    customer = openapi.Parameter('customer_id', openapi.IN_QUERY, description="Customer ID",
                                 type=openapi.TYPE_STRING)

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['customer'], request_body=CustomerAddressSerializer,
                         responses={'500': GENERAL_ERROR, '200': CustomerAddressSerializer})
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


class ProductListing(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    customer = openapi.Parameter('shop_id', openapi.IN_QUERY, description="Shop ID",
                                 type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['customer'], manual_parameters=[customer],
                         responses={'500': GENERAL_ERROR, '200': ProductSerializer})
    def get(self, request):
        try:
            shop = Shop.objects.get(id=request.GET.get('shop_id'))
            products = shop.shop_products.all()
            serializer = ProductSerializer(products, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'orders': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class CustomerSignup(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['customer'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
        }))
    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        try:
            if request.data.get('is_customer', ' '):
                role = USER_TYPE_CHOICES.customer
            else:
                role = USER_TYPE_CHOICES.vendor
            user, created = AppUser.objects.get_or_create(
                username=mobile_number,
                mobile_number=mobile_number,
                defaults={'role': role, 'is_active': False, 'email': request.data.get('email'),
                          'first_name': request.data.get('name')},
            )
            Customer.objects.get_or_create(user=user)
            if created:
                otp = OTPgenerator()
                deliver_sms(mobile_number, otp)
                user.verification_otp = otp
                user.save()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={'user_id': user.id,
                                               'user_type': user.role
                                               })
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class AccountEditView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['customer'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
        }))
    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        try:
            user = AppUser.objects.get(id=request.user.id)
            if user.mobile_number != mobile_number:
                otp = OTPgenerator()
                deliver_sms(mobile_number, otp)
                user.verification_otp = otp
                user.mobile_number = mobile_number
            else:
                user.email = request.data.get('mobile_number')
            user.save()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={'user_id': user.id,
                                               'user_type': user.role
                                               })
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class CustomerFavouriteView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['customer'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'is_favourite': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        }))
    def post(self, request):
        from product.models import Product
        try:
            product = Product.objects.get(id=request.data.get('product_id'))
            if request.data.get('is_favourite') == 'true':
                CustomerFavouriteProduct.objects.get_or_create(product=product, customer__user=request.user)
            else:
                CustomerFavouriteProduct.objects.get(product=product, customer__user=request.user).delete()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={})
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
