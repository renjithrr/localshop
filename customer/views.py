import logging
import requests
import json
from geopy import Nominatim
from django.utils import timezone

from datetime import datetime, timedelta
from fcm_django.models import FCMDevice
from pyfcm import FCMNotification
from django.contrib.gis.measure import D
from django.contrib.gis.geos import *
from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework. viewsets import GenericViewSet
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from user.models import Shop
from customer.serializers import NearbyShopSerializer, CustomerOrderSerializer, CustomerAddressSerializer, \
    CustomerProductSerializer, VarientSerializer, CustomerShopSerializer, ShopBannerSerializer,\
    CustomerOrderHistorySerializer, CustomerProductSearchSerializer, ServiceAreaSerializer
from utilities.mixins import ResponseViewMixin
from utilities.messages import SUCCESS, GENERAL_ERROR
from utilities.utils import deliver_sms, OTPgenerator, payment_calculation
from user.models import ShopCategory, AppUser, AppConfigData, ServiceArea, Coupon,\
    DELIVERY_CHOICES, USER_TYPE_CHOICES
from customer.models import Customer, Address, CustomerFavouriteProduct, Order, PAYMENT_STATUS, ORDER_STATUS,\
    PAYMENT_CHOICES, OrderItem
from product.models import Product, Category, ProductVarient

db_logger = logging.getLogger('db')


class NearbyShop(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    latitude = openapi.Parameter('latitude', openapi.IN_QUERY, description="latitude",
                                   type=openapi.TYPE_STRING)
    longitude = openapi.Parameter('longitude', openapi.IN_QUERY, description="longitude",
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
            distance = AppConfigData.objects.get(key='SHOP_BASE_RADIUS').value
            query_set = Shop.objects.filter(location__distance_lte=(location, D(km=int(distance))))
            if request.GET.get('shop_category', ''):
                query_set = query_set.filter(shop_category=request.GET.get('shop_category', ''))
            serializer = NearbyShopSerializer(query_set, context={'location': location}, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'shops': serializer.data},
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class CommonParamsView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            shop_choices = [{'id': shop.id, 'category': shop.name, 'card_type': shop.card_type}
                            for shop in ShopCategory.objects.all()]
            # payment_methods = [{'id': method.id, 'method': method.payment_type}
            #                    for method in PaymentMethod.objects.all()]
            return self.success_response(code='HTTP_200_OK',
                                         data={'shopcategories': shop_choices,
                                               # 'payment_methods': payment_methods
                                               },
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class OrderHistoryView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    # token = openapi.Parameter('customer_id', openapi.IN_QUERY, description="Pass token in headers",
    #                              type=openapi.TYPE_STRING)

    # @swagger_auto_schema(tags=['customer'], manual_parameters=[token],
    #                      responses={'500': GENERAL_ERROR, '200': CustomerOrderSerializer})
    def get(self, request):
        try:

            customer = Customer.objects.get(user=request.user)
            orders = customer.customer_orders.all().order_by('-id')
            serializer = CustomerOrderHistorySerializer(orders, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'orders': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:

            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class CustomerAddressView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerAddressSerializer
    customer = openapi.Parameter('customer_id', openapi.IN_QUERY, description="Customer ID",
                                 type=openapi.TYPE_STRING)

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['customer'], request_body=CustomerAddressSerializer,
                         responses={'500': GENERAL_ERROR, '200': CustomerAddressSerializer})
    def create(self, request):
        try:
            print(request.data)
            address = Address.objects.get(id=request.data.get('id'))
            serializer = CustomerAddressSerializer(instance=address, data=request.data)
        except Address.DoesNotExist:
            serializer = CustomerAddressSerializer(data=request.data)
        if serializer.is_valid():
            address = serializer.save()
            customer = Customer.objects.get(user=request.user)
            address.customer = customer
            address.save()
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        else:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    @swagger_auto_schema(tags=['product'], manual_parameters=[customer])
    def list(self, request, *args, **kwargs):
        try:
            adresses = Address.objects.filter(customer=Customer.objects.get(user=request.user), is_deleted=False)
            serializer = CustomerAddressSerializer(adresses, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
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


    def delete(self, request, pk=None):
        try:
            address = Address.objects.get(id=request.data.get('id', ''))
            address.is_deleted = True
            address.save()
            return self.success_response(code='HTTP_200_OK',
                                         data={},
                                         message=SUCCESS)
        except Address.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductListing(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    # latitude = openapi.Parameter('latitude', openapi.IN_QUERY, description="latitude",
    #                              type=openapi.TYPE_STRING)
    # longitude = openapi.Parameter('longitude', openapi.IN_QUERY, description="longitude",
    #                               type=openapi.TYPE_STRING)
    shop_id = openapi.Parameter('shop_id', openapi.IN_QUERY, description="shop_id",
                                  type=openapi.TYPE_STRING)
    search = openapi.Parameter('search', openapi.IN_QUERY, description="search products",type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[shop_id, search])
    def get(self, request):
        try:
            # latitude = request.GET.get('latitude', 0)
            # longitude = request.GET.get('longitude', 0)
            # location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
            # distance = AppConfigData.objects.get(key='SHOP_BASE_RADIUS').value
            # shops = Shop.objects.filter(location__distance_lte=(location, D(km=int(distance))))
            # if request.GET.get('search', ''):
            #     searched_shops = shops.filter(business_name__icontains=request.GET.get('search', ''))
            #     shop_serializer = NearbyShopSerializer(searched_shops, context={'location': location}, many=True)
            #     products = Product.objects.filter(shop__in=list(shops.values_list('id', flat=True)))
            shop = Shop.objects.get(id=request.GET.get('shop_id'))
            search = request.GET.get('search', '')
            # products = shop.shop_products.filter(is_hidden=False, is_deleted=False)
            categories = Category.objects.filter(product__isnull=False, product__shop=shop)
            product_serializer = CustomerProductSerializer(categories, context={'shop': shop, 'search': search},
                                                           many=True)
            # product_serializer = CustomerProductSerializer(products, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'products': product_serializer.data,
                                               },
                                     message=SUCCESS)
        # return self.success_response(code='HTTP_200_OK',
        #                              data={
        #                                    },
        #                              message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
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
            user= AppUser.objects.get(
                mobile_number=mobile_number,
                role=USER_TYPE_CHOICES.customer
            )
            Customer.objects.get_or_create(user=user)
            otp = OTPgenerator()
            # deliver_sms(mobile_number, otp)
            deliver_sms.apply_async(queue='normal', args=(mobile_number, otp),
                                    kwargs={})
            user.verification_otp = otp
            user.email = request.data.get('email')
            user.first_name = request.data.get('name')
            user.save()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={'user_id': user.id,
                                               'user_type': user.role
                                               })
        except Exception as e:
            db_logger.exception(e)
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
                # deliver_sms(mobile_number, otp)
                deliver_sms.apply_async(queue='normal', args=(mobile_number, otp),
                                        kwargs={})
                user.verification_otp = otp
                user.mobile_number = mobile_number
            user.email = request.data.get('email')
            user.first_name = request.data.get('name')
            user.save()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={'user_id': user.id,
                                               'user_type': user.role
                                               })
        except Exception as e:
            db_logger.exception(e)
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
                CustomerFavouriteProduct.objects.get_or_create(product=product,
                                                               customer=Customer.objects.get(user=request.user))
            else:
                CustomerFavouriteProduct.objects.get(product=product,
                                                     customer=Customer.objects.get(user=request.user)).delete()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={})
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductVarientView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    product_id = openapi.Parameter('product_id', openapi.IN_QUERY, description="Product ID",
                                 type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['customer'], manual_parameters=[product_id],
                         responses={'500': GENERAL_ERROR, '200': VarientSerializer})
    def get(self, request):
        try:
            product = Product.objects.get(id=request.GET.get('product_id'))
            products = product.product_varients.all()
            serializer = VarientSerializer(products, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'orders': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class OrderView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    product_id = openapi.Parameter('order_id', openapi.IN_QUERY, description="Order ID",
                                 type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['customer'], manual_parameters=[product_id],
                         responses={'500': GENERAL_ERROR, '200': VarientSerializer})
    def get(self, request):
        try:
            order = Order.objects.get(id=request.GET.get('order_id'))
            serializer = CustomerOrderSerializer(order)
            return self.success_response(code='HTTP_200_OK',
                                         data={'order_details': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class ShopView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    shop_id = openapi.Parameter('shop_id', openapi.IN_QUERY, description="Shop ID",
                                 type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['customer'], manual_parameters=[shop_id],
                         responses={'500': GENERAL_ERROR, '200': CustomerShopSerializer})
    def get(self, request):
        try:
            shop = Shop.objects.get(id=request.GET.get('shop_id'))
            if request.user.is_anonymous:
                serializer = CustomerShopSerializer(shop, context={'user': None})
            else:
                serializer = CustomerShopSerializer(shop, context={'user': request.user})
            return self.success_response(code='HTTP_200_OK',
                                         data={'shop_details': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class BannerView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            shop = Shop.objects.all()
            serializer = ShopBannerSerializer(shop, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'shop_details': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class TrendingShopsView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    latitude = openapi.Parameter('latitude', openapi.IN_QUERY, description="latitude",
                                   type=openapi.TYPE_STRING)
    longitude = openapi.Parameter('longitude', openapi.IN_QUERY, description="longitude",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[latitude, longitude],
                         responses={'500': GENERAL_ERROR, '200': NearbyShopSerializer})
    def get(self, request):
        try:

            latitude = request.GET.get('latitude', 0)
            longitude = request.GET.get('longitude', 0)
            location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
            distance = AppConfigData.objects.get(key='SHOP_BASE_RADIUS').value
            query_set = Shop.objects.filter(location__distance_lte=(location, D(km=int(distance))))
            if request.GET.get('shop_category', ''):
                query_set = query_set.filter(shop_category=request.GET.get('shop_category', ''))
            serializer = NearbyShopSerializer(query_set, context={'location': location}, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'shops': serializer.data},
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class IsRepeatPossibleView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    order_id = openapi.Parameter('order_id', openapi.IN_QUERY, description="Order ID",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[order_id])
    def get(self, request):
        try:

            order_id = request.GET.get('order_id', 0)
            order = Order.objects.get(id=order_id)
            order_items = order.order_items.all()
            available = True
            for value in order_items:
                if value.quantity < value.product_id.quantity:
                    continue
                else:
                    available = False
                    break
            return self.success_response(code='HTTP_200_OK',
                                         data={'is_repeat_possible': available},
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class IsDeliveryAvailableView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    address_id = openapi.Parameter('address_id', openapi.IN_QUERY, description="Address ID",
                                    type=openapi.TYPE_STRING)
    shop_id = openapi.Parameter('shop_id', openapi.IN_QUERY, description="Shop ID",
                                   type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[address_id, shop_id])
    def get(self, request):
        try:

            address_id = request.GET.get('address_id', '')
            shop_id = request.GET.get('shop_id', '')
            shop = Shop.objects.get(id=shop_id)
            address = Address.objects.get(id=address_id)
            latitude = address.lat
            longitude = address.long
            location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
            distance = AppConfigData.objects.get(key='SHOP_BASE_RADIUS').value
            distance1 = shop.location.distance(location)
            if float(distance) > distance1:
                is_delivery_available = True
            else:
                is_delivery_available = False
            return self.success_response(code='HTTP_200_OK',
                                         data={'is_delivery_available': is_delivery_available},
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class IsUnderServiceAreaView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    address_id = openapi.Parameter('address_id', openapi.IN_QUERY, description="Address ID",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[address_id])
    def get(self, request):
        try:

            address_id = request.GET.get('address_id', '')
            address = Address.objects.get(id=address_id)
            latitude = address.lat
            longitude = address.long
            location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
            distance = AppConfigData.objects.get(key='SHOP_BASE_RADIUS').value
            distance1 = ServiceArea.objects.last().location.distance(location)
            if float(distance) > distance1:
                is_under_service_area = True
            else:
                is_under_service_area = False
            return self.success_response(code='HTTP_200_OK',
                                         data={'is_under_service_area': is_under_service_area},
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ApplyCouponView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    # @swagger_auto_schema(tags=['customer'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
    #         'name': openapi.Schema(type=openapi.TYPE_STRING),
    #         'email': openapi.Schema(type=openapi.TYPE_STRING),
    #     }))
    def post(self, request):
        # address_id = request.data.get('address_id')
        products = request.data.get('products')
        discount = None
        total_amount = 0
        shop = None
        offer_prize = None
        shipping_charge = None
        try:
            for value in products:
                try:
                    product = Product.objects.get(id=value['id'])
                except Exception as e:
                    product = ProductVarient.objects.get(id=value['id'])
                if value.get('bargain_amount'):
                    if product.lowest_selling_rate < value.get('bargain_amount') < product.highest_selling_rate:
                        total_amount += value.get('bargain_amount') * value['quantity']
                else:
                    total_amount += product.mrp * value['quantity']
                shop = product.shop
            try:
                coupon = Coupon.objects.get(shops=shop, is_active=True, code=request.data.get('coupon_code'))
            except Exception as e:
                coupon = None
            if coupon:
                if coupon.is_percentage:
                    discount = total_amount * (coupon.discount/100)
                    offer_prize = total_amount - discount
                else:
                    discount = coupon.discount
                    offer_prize = total_amount - discount

            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={'coupon_discount': discount,
                                               'total':offer_prize,
                                               'shipping_charge': shipping_charge
                                               })
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class DeliveryChargeView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    address_id = openapi.Parameter('address_id', openapi.IN_QUERY, description="Address ID",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[address_id])
    def post(self, request):
        try:

            address_id = request.data.get('address_id', '')
            address = Address.objects.get(id=address_id)
            latitude = address.lat
            longitude = address.long
            location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
            distance = AppConfigData.objects.get(key='SHOP_BASE_RADIUS').value
            shop_id = request.data.get('shop_id', '')
            shop = Shop.objects.get(id=shop_id)
            distance1 = shop.location.distance(location)
            service_available_now = True
            if float(distance) < distance1:
                return self.success_response(code='HTTP_200_OK',
                                             data={'is_delivery_available': False},
                                             message=SUCCESS)
            delivery_charge = 0

            total_amount = 0
            products = request.data.get('products')
            for value in products:
                try:
                    product = Product.objects.get(id=value['id'])
                except Exception as e:
                    product = ProductVarient.objects.get(id=value['id'])

                total_amount += product.mrp * value['quantity']

            delivery_details = shop.shop_delivery_options.last()
            try:
                # payment_calculation(total_amount, delivery_details)
                delivery_type = delivery_details.delivery_type
                delivery_type = list(map(int, delivery_type))
                if DELIVERY_CHOICES.self_delivery in delivery_type:
                    delivery_charge = delivery_details.delivery_charge
                elif DELIVERY_CHOICES.townie_ship in delivery_type:
                    if delivery_details.free_delivery_for and float(total_amount) >= delivery_details.free_delivery_for:
                        delivery_charge = 0
                        townie_time = shop.service_area.townie_delivery_end
                        diff = datetime.combine(datetime.today(), townie_time) - datetime.now()
                        if diff.total_seconds() < 0:
                            service_available_now = False
                        else:
                            service_available_now = True
                    else:
                        delivery_charge = AppConfigData.objects.get(key='TOWNIE_CHARGE').value
                elif DELIVERY_CHOICES.bulk_delivery in delivery_type:
                    delivery_charge = 0

            except Exception as e:
                db_logger.exception(e)

            return self.success_response(code='HTTP_200_OK',
                                         data={'delivery_charge': delivery_charge,
                                               'service_available_now': service_available_now},
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class GenerateTokenView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    address_id = openapi.Parameter('address_id', openapi.IN_QUERY, description="Address ID",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[address_id])
    def post(self, request):
        try:

            address_id = request.data.get('address_id', '')
            # address = Address.objects.get(id=address_id)
            token = ''
            coupon_applied = False
            shop_id = request.data.get('shop_id', '')
            total_amount = 0
            delivery_charge = 0
            total = 0
            rate = 0
            shop = Shop.objects.get(id=shop_id)
            products = request.data.get('products')
            order = Order.objects.create(payment_status=PAYMENT_STATUS.pending,
                                         status=ORDER_STATUS.pending, shop=shop,
                                         customer=Customer.objects.get(user=request.user))
            for value in products:
                try:
                    product = Product.objects.get(id=value['id'])
                except Exception as e:
                    product = ProductVarient.objects.get(id=value['id'])
                if value['quantity'] > product.quantity:
                    return self.success_response(code='HTTP_200_OK',
                                                 data={'product_not_available': 'product ' + product.name +
                                                                                ' is not available',
                                                       'quantity_left': product.quantity},
                                                 message=SUCCESS)
                if value.get('bargain_amount'):
                    if product.lowest_selling_rate < value.get('bargain_amount') < product.highest_selling_rate:
                        total = value.get('bargain_amount') * value['quantity']
                        rate = value.get('bargain_amount')
                        total_amount += total
                elif product.offer_prize:
                    total = product.offer_prize * value['quantity']
                    rate = product.offer_prize
                    total_amount += total
                else:
                    # print(product.mrp, product.lowest_selling_rate, product.highest_selling_rate)
                    total = product.mrp * value['quantity']
                    rate = product.mrp
                    total_amount += total
                OrderItem.objects.create(product_id=product, quantity=value['quantity'], rate=rate,
                                         total=total, order_id=order)
            # otp = OTPgenerator()
            if request.data.get('coupon_code'):
                try:
                    coupon = Coupon.objects.get(shops=shop, is_active=True, code=request.data.get('coupon_code'))
                except Exception as e:
                    coupon = None
                if coupon:
                    if coupon.is_percentage:
                        discount = total_amount * (coupon.discount/100)
                        total_amount = total_amount - discount
                    else:
                        discount = coupon.discount
                        total_amount = total_amount - discount
                    order.discount = discount
                    coupon_applied = True


            order.grand_total = total_amount
            order.save()
            headers = {
                'Content-Type': 'application/json',
                'x-client-id': '25883f6357f2b14a1885899db38852',
                'x-client-secret': '12ef6556720eccd161ca5d6de2e272ac034a53f0',
            }

            data = json.dumps({ "orderId": order.id, "orderAmount":total_amount, "orderCurrency":"INR" })
            payment_type = request.data.get('payment_type', '')
            if payment_type == 'online':
                response = requests.post('https://test.cashfree.com/api/v2/cftoken/order', headers=headers, data=data)
                res = response.json()
                token = res['cftoken']
                order.cod = False
                # otp = OTPgenerator()
                # order.customer_otp = otp
                # order.save()
            else:
                order.payment_type = PAYMENT_CHOICES.cod
                # order.save()
            order.delivery_type = request.data.get('delivery_type')
            order.save()
            delivery_details = shop.shop_delivery_options.last()
            delivery_type = int(request.data.get('delivery_type'))
            try:
                if delivery_type == DELIVERY_CHOICES.self_delivery:
                    delivery_charge = delivery_details.delivery_charge
                elif delivery_type == DELIVERY_CHOICES.townie_ship:
                    if float(total_amount) >= delivery_details.free_delivery_for:
                        delivery_charge = 0
                    else:
                        delivery_charge = AppConfigData.objects.get(key='TOWNIE_CHARGE').value
                elif delivery_type == DELIVERY_CHOICES.bulk_delivery:
                    delivery_charge = 0
            except Exception as e:
                pass
            townie_payment, vendor_payment = payment_calculation(total_amount,delivery_type,  delivery_details)
            vendor_split = [{'vendorId': '', 'commissionAmount': townie_payment},
                            {'vendorId': '', 'commissionAmount': vendor_payment}]
            data = {'order_id': order.id, 'token': token, 'total_amount': total_amount, 'currency': 'INR',
                    'shipping_charge': delivery_charge, 'discount': order.discount, 'vendor_split': vendor_split,
                    'coupon_applied': coupon_applied}
            try:
                if payment_type != 'online':
                    # device = FCMDevice.objects.filter(user=request.user, active=True).registration_id
                    device = FCMDevice.objects.filter(user=order.shop.user, active=True).values_list('registration_id',
                                                                                           flat=True)
                    message = {'data': {'order_id': order.id}, 'type': 'new_order','body': 'A new order has placed'}
                    push_service = FCMNotification(api_key=settings.FCM_KEY)
                    # response = push_service.notify_single_device(registration_id=device, data_message=message)
                    response = push_service.notify_multiple_devices(registration_ids=list(device), data_message=message)
                    db_logger.debug('push service to : {0} => {1}==>{2}'.format(order.id, str(response),
                                                                                order.shop.user))
            except Exception as e:
                logging.exception(e)
            return self.success_response(code='HTTP_200_OK',
                                         data=data,
                                         message=SUCCESS)

        except Exception as e:
            db_logger.exception(e)

            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class PaymentUpdateView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    order_id = openapi.Parameter('order_id', openapi.IN_QUERY, description="Order ID",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[order_id])
    def post(self, request):
        try:

            order = Order.objects.get(id=request.data.get('order_id'))
            order.payment_status = request.data.get('payment_status')
            if request.data.get('payment_status', ''):
                order.payment_message = request.data.get('payment_status')
            order.save()
            try:
                if order.payment_status == PAYMENT_STATUS.completed:
                    vendor = order.shop.user
                    # device = FCMDevice.objects.filter(user=request.user, active=True).registration_id
                    device = FCMDevice.objects.filter(user=vendor, active=True).values_list('registration_id',
                                                                                           flat=True)
                    message = {'data': {'order_id': order.id}, 'type': 'new_order','body': 'A new order has placed'}
                    push_service = FCMNotification(api_key=settings.FCM_KEY)
                    # response = push_service.notify_single_device(registration_id=device, data_message=message)
                    response = push_service.notify_multiple_devices(registration_ids=list(device), data_message=message)
                    db_logger.debug('push service to : {0} => {1}==>{2}'.format(order.id, str(response), order.shop.user))
            except Exception as e:
                logging.exception(e)

            return self.success_response(code='HTTP_200_OK',
                                         data={},
                                         message=SUCCESS)

        except Exception as e:
            db_logger.exception(e)

            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class GetLocationView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    # order_id = openapi.Parameter('order_id', openapi.IN_QUERY, description="Order ID",
    #                                 type=openapi.TYPE_STRING)
    # @swagger_auto_schema(tags=['customer'], manual_parameters=[order_id])
    def get(self, request):
        try:
            # locator = Nominatim(user_agent="myGeocoder")
            # coordinates = str(request.GET.get('latitude')) + ', ' + str(request.GET.get('longitude'))
            # location = locator.reverse(coordinates)
            # locations = ', '.join(location.raw['display_name'].split(', ')[:2])
            # return self.success_response(code='HTTP_200_OK',
            #                              data={'location': locations,
            #                                    'id': location.raw['place_id']},
            #                              message=SUCCESS)
                location_list = []
                id_list = []
                latitude = request.GET.get('latitude')
                longitude = request.GET.get('longitude')
                location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
                base_distance = AppConfigData.objects.get(key='SERVICE_AREA_BASE_RADIUS').value
                for value in ServiceArea.objects.all():
                    distance = value.location.distance(location)
                    if distance <= float(base_distance):
                        location_list.append(distance)
                        id_list.append(value.id)
                try:
                    index = location_list.index(min(location_list))
                    location = ServiceArea.objects.get(id=id_list[index])
                    serializer = ServiceAreaSerializer(location)
                    data = serializer.data
                except Exception as e:
                    data = {}
                return self.success_response(code='HTTP_200_OK',
                                             data=data,
                                             message=SUCCESS)

        except Exception as e:
            db_logger.exception(e)
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message='location not available')


class GetAllLocationView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    # order_id = openapi.Parameter('order_id', openapi.IN_QUERY, description="Order ID",
    #                                 type=openapi.TYPE_STRING)
    # @swagger_auto_schema(tags=['customer'], manual_parameters=[order_id])
    # @swagger_auto_schema(tags=['customer'], manual_parameters=[address_id])
    def get(self, request):
        try:
            # location_list = []
            # latitude = request.GET.get('latitude')
            # longitude = request.GET.get('longitude')
            # location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
            # distance = AppConfigData.objects.get(key='SERVICE_AREA_BASE_RADIUS').value
            service_areas = ServiceArea.objects.all()
            if 'search' in request.GET:
                service_areas = service_areas.filter(name__icontains=request.GET.get('search'))
            serializer = ServiceAreaSerializer(service_areas, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class SearchProductView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    # latitude = openapi.Parameter('latitude', openapi.IN_QUERY, description="latitude",
    #                              type=openapi.TYPE_STRING)
    # longitude = openapi.Parameter('longitude', openapi.IN_QUERY, description="longitude",
    #                               type=openapi.TYPE_STRING)
    shop_id = openapi.Parameter('shop_id', openapi.IN_QUERY, description="shop_id",
                                  type=openapi.TYPE_STRING)
    search = openapi.Parameter('search', openapi.IN_QUERY, description="search products",type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[shop_id, search])
    def get(self, request):
        try:
            # latitude = request.GET.get('latitude', 0)
            # longitude = request.GET.get('longitude', 0)
            # location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
            # distance = AppConfigData.objects.get(key='SHOP_BASE_RADIUS').value
            # shops = Shop.objects.filter(location__distance_lte=(location, D(km=int(distance))))
            searched_shops = Shop.objects.filter(shop_name__icontains=request.GET.get('keyword', ''))
            shop_serializer = NearbyShopSerializer(searched_shops, many=True)
            products = Product.objects.filter(name__icontains=request.GET.get('keyword', ''),
                                              is_hidden=False, is_deleted=False)
        # products = shop.shop_products.filter(is_hidden=False, is_deleted=False)
            product_serializer = CustomerProductSearchSerializer(products, many=True)
            # product_serializer = CustomerProductSerializer(products, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'products': product_serializer.data,
                                               'shops': shop_serializer.data
                                               },
                                     message=SUCCESS)
        # return self.success_response(code='HTTP_200_OK',
        #                              data={
        #                                    },
        #                              message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class TrendingOfferView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    latitude = openapi.Parameter('latitude', openapi.IN_QUERY, description="latitude",
                                   type=openapi.TYPE_STRING)
    longitude = openapi.Parameter('longitude', openapi.IN_QUERY, description="longitude",
                                    type=openapi.TYPE_STRING)
    @swagger_auto_schema(tags=['customer'], manual_parameters=[latitude, longitude],
                         responses={'500': GENERAL_ERROR, '200': NearbyShopSerializer})
    def get(self, request):
        try:
            coupon = Coupon.objects.filter(is_active=True)
            query_set = Shop.objects.filter(id__in=coupon.values_list('shops', flat=True))
            serializer = ShopBannerSerializer(query_set, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'shops': serializer.data},
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class FavouriteProductView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    # @swagger_auto_schema(tags=['customer'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'is_favourite': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    #         'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
    #     }))
    def get(self, request):
        from product.models import Product
        try:
            customer_favourites = \
                CustomerFavouriteProduct.objects.filter(customer=Customer.objects.get(user=request.user))
            # print(customer_favourites)
            products = Product.objects.filter(id__in=list(customer_favourites.values_list('product_id', flat=True)),
                                              is_hidden=False, is_deleted=False)
            keyword = request.GET.get('keyword', '')
            if keyword:
                products = products.filter(name__icontains=request.GET.get('keyword', ''))
            # products = shop.shop_products.filter(is_hidden=False, is_deleted=False)
            product_serializer = CustomerProductSearchSerializer(products, many=True)
            # product_serializer = CustomerProductSerializer(products, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'products': product_serializer.data
                                               },
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class BargainPriceView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    # @swagger_auto_schema(tags=['customer'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'is_favourite': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    #         'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
    #     }))
    def get(self, request):
        from product.models import Product
        try:
            product = Product.objects.get(id=request.GET.get('product_id', ''))
            customer = Customer.objects.get(user=request.user)
            bargain_amount = request.GET.get('bargain_amount', 0)
            if customer.bargain_count < 4:
                if product.is_bargain_possible:
                    if product.lowest_selling_rate <= float(bargain_amount) <= product.highest_selling_rate:
                            bargain_amount_viable = True
                            data = {
                                      'bargain_amount_viable': bargain_amount_viable,
                                      'bargain_limit_reached': False
                                  },
                    else:
                        bargain_amount_viable = False
                        data = {
                                  'bargain_amount_viable': bargain_amount_viable,
                                  'bargain_limit_reached': False
                              }
                    customer.bargain_count += 1
                    customer.save()
                    return self.success_response(code='HTTP_200_OK',
                                                 data=data,
                                                 message=SUCCESS)
                else:
                    return self.success_response(code='HTTP_200_OK',
                                                 data={'is_bargain_possible': False
                                                       },
                                                 message=SUCCESS)
            else:
                if customer.bargain_upto:
                    if customer.bargain_upto < timezone.now() and customer.bargain_count == 4:
                        customer.bargain_count = 0
                        customer.save()
                        if product.is_bargain_possible:
                            if product.lowest_selling_rate <= float(bargain_amount) <= product.highest_selling_rate:
                                bargain_amount_viable = True
                                data = {
                                           'bargain_amount_viable': bargain_amount_viable,
                                           'bargain_limit_reached': False
                                       },
                            else:
                                bargain_amount_viable = False
                                data = {
                                    'bargain_amount_viable': bargain_amount_viable,
                                    'bargain_limit_reached': False
                                }
                            customer.bargain_count += 1
                            customer.save()
                            return self.success_response(code='HTTP_200_OK',
                                                         data=data,
                                                         message=SUCCESS)
                        else:
                            return self.success_response(code='HTTP_200_OK',
                                                         data={'is_bargain_possible': False
                                                               },
                                                         message=SUCCESS)
                    else:
                        return self.success_response(code='HTTP_200_OK',
                                                     data={'bargain_limit_reached': True
                                                           },
                                                     message=SUCCESS)
                else:
                    customer.bargain_upto = datetime.now() + timedelta(days=1)
                    customer.save()
                return self.success_response(code='HTTP_200_OK',
                                             data={'bargain_limit_reached': True
                                                   },
                                             message=SUCCESS)


        except Exception as e:
            db_logger.exception(e)
            # print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

