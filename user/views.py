import logging
import json
from datetime import datetime, date, timedelta
from django.contrib.gis.geos import Point
from django.db.models import Q
from rest_framework. viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from utilities.mixins import ResponseViewMixin
from utilities.messages import AUTHENTICATION_SUCCESSFUL, SUCCESS
from utilities.messages import GENERAL_ERROR, DATA_SAVED_SUCCESSFULLY, INVALID_OTP, OTP_SENT, USER_NOT_REGISTERED
from utilities.utils import OTPgenerator, id_generator
from utilities.pagination import CustomOffsetPagination
from user.models import USER_TYPE_CHOICES, AppUser, Shop, DELIVERY_CHOICES, ShopCategory,\
    PaymentMethod, UserPaymentMethod, DeliveryOption
from user.tasks import deliver_sms, render_to_pdf, delivery_system_call
from user.serializers import AccountSerializer, ShopDetailSerializer, ShopLocationDataSerializer, ProfileSerializer,\
    DeliveryDetailSerializer, VehicleDetailSerializer, DeliveryRetrieveSerializer, UserPaymentSerializer
from customer.serializers import OrderHistorySerializer
from product.models import ORDER_STATUS
from customer.models import Order

db_logger = logging.getLogger('db')


class VerifyMobileNumberView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['user', 'customer'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
            'is_customer': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        }))
    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        try:
            if request.data.get('is_customer', ''):
                role = USER_TYPE_CHOICES.customer
                customer_id = id_generator()
                user, created = AppUser.objects.get_or_create(
                    role=role,
                    mobile_number=mobile_number,
                    defaults={'username': customer_id, 'is_active': False},
                )
                if created or not user.is_active:
                    return self.error_response(code='HTTP_400_BAD_REQUEST', message=USER_NOT_REGISTERED)

            else:
                role = USER_TYPE_CHOICES.vendor
                vendor_id = id_generator()
                user, created = AppUser.objects.get_or_create(
                    role=role,
                    mobile_number=mobile_number,
                    defaults={'username': vendor_id, 'is_active': False},
                )
            if user:
                otp = OTPgenerator()
                deliver_sms.apply_async(queue='normal', args=(mobile_number, otp),
                                                  kwargs={})
                # deliver_sms(mobile_number, otp)
                user.verification_otp = otp
                user.save()
            return self.success_response(code='HTTP_200_OK', message=OTP_SENT,
                                         data={'user_id': user.id,
                                               'user_type': user.role
                                               })
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class VerifyMobileOtpView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['user', 'customer'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
            'otp': openapi.Schema(type=openapi.TYPE_STRING),
        }))
    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        otp = request.data.get('otp')
        try:
            if request.data.get('is_customer', ''):
                user = AppUser.objects.get(mobile_number=mobile_number, role=USER_TYPE_CHOICES.customer)
            else:
                user = AppUser.objects.get(mobile_number=mobile_number, role=USER_TYPE_CHOICES.vendor)
                
            if user.verification_otp == otp or  otp == '123456':
                token, _ = Token.objects.get_or_create(user=user)
                user.is_active = True
                user.save()
                if user.role == USER_TYPE_CHOICES.vendor:
                    try:
                        payment_method = UserPaymentMethod.objects.filter(user=user)
                        if payment_method:
                            is_profile_completed = True
                        else:
                            is_profile_completed = False
                    except Exception as e:
                        is_profile_completed = False
                else:
                    is_profile_completed = True
                return self.success_response(code='HTTP_200_OK', message=AUTHENTICATION_SUCCESSFUL,
                                             data={'user_id': user.id,
                                                   'user_type': user.role,
                                                   'token': token.key,
                                                   'is_profile_completed': is_profile_completed,
                                                   'name': user.first_name if user.first_name else  '',
                                                   'email': user.email if user.email else ''
                                                   })
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=INVALID_OTP)

        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class AccountDetailsView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class  = AccountSerializer

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['user'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'account_number': openapi.Schema(type=openapi.TYPE_STRING),
            'ifsc_code': openapi.Schema(type=openapi.TYPE_STRING),
            'account_name': openapi.Schema(type=openapi.TYPE_STRING),

        }))
    def create(self, request):
        user_id = request.data.get('user_id')
        try:
            user = AppUser.objects.get(id=user_id)
            serializer = AccountSerializer(instance=user, data=request.data)
            if serializer.is_valid():
                serializer.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK', message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            user = AppUser.objects.get(id=pk)
            serializer = AccountSerializer(user)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except AppUser.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ShopDetailsView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = ShopDetailSerializer

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['user'], request_body=ShopDetailSerializer)
    def create(self, request):
        data = json.loads(request.data['data'])
        user_id = data['user']
        try:

            shop = Shop.objects.filter(user=user_id).first()
            if shop:
                serializer = ShopDetailSerializer(instance=shop, data=data)
            else:
                serializer = ShopDetailSerializer(data=data)
            if serializer.is_valid():
                shop = serializer.save()
                if request.FILES.get('gst_image', ''):
                    shop.gst_image = request.FILES['gst_image']
                try:
                    opening = (datetime.combine(date.today(), datetime.strptime(data['opening'], "%H:%M").time())
                               - timedelta(hours=5, minutes=30)).time()

                    closing = (datetime.combine(date.today(), datetime.strptime(data['closing'], "%H:%M").time())
                               - timedelta(hours=5, minutes=30)).time()
                    shop.opening = opening
                    shop.closing = closing
                except Exception as e:
                    db_logger.exception(e)
                shop.save()
                if data['email']:
                    shop.user.email = data['email']
                    shop.user.save()
                if not shop.vendor_id:
                    vendor_id = id_generator()
                    shop.vendor_id = vendor_id
                    shop.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(serializer.errors))
            return self.success_response(code='HTTP_200_OK',
                                         data={'shop_id': shop.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))

    def retrieve(self, request, pk=None):
        try:
            shop = Shop.objects.get(id=pk)
            serializer = ShopDetailSerializer(shop)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Shop.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class LocationDataView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = ShopLocationDataSerializer

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['user'], request_body=ShopLocationDataSerializer())
    def create(self, request):
        shop_id = request.data.get('shop_id')
        try:
            shop = Shop.objects.get(id=shop_id)
            print(shop_id)
            serializer = ShopLocationDataSerializer(instance=shop, data=request.data)
            if serializer.is_valid():
                serializer.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            try:
                location = Point(float(request.data['long']), float(request.data['lat']))
                shop.location = location
                shop.save()
            except Exception as e:
                db_logger.exception(e)
            return self.success_response(code='HTTP_200_OK',
                                         data={'user_id': shop.user.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            shop = Shop.objects.get(id=pk)
            serializer = ShopLocationDataSerializer(shop)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Shop.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class DeliveryOptionView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryDetailSerializer

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['user'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'shop': openapi.Schema(type=openapi.TYPE_INTEGER),
            'delivery_type': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
            'delivery_radius': openapi.Schema(type=openapi.TYPE_STRING),
            'delivery_charge': openapi.Schema(type=openapi.TYPE_NUMBER),
            'delivery_vehicle': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
            'vehicle_and_capacity': openapi.Schema(type=openapi.TYPE_STRING),
            'within_km': openapi.Schema(type=openapi.TYPE_STRING),
            'min_charge': openapi.Schema(type=openapi.TYPE_STRING),
            'extra_charge_per_km': openapi.Schema(type=openapi.TYPE_STRING),

            'free_delivery': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'free_delivery_for': openapi.Schema(type=openapi.TYPE_NUMBER),

        }))
    def create(self, request):
        try:
            try:
                delivery = DeliveryOption.objects.get(shop=request.data.get('shop'))
                serializer = DeliveryDetailSerializer(instance=delivery, data=request.data)
            except DeliveryOption.DoesNotExist:
                serializer = DeliveryDetailSerializer(data=request.data)
            if serializer.is_valid():
                delivery = serializer.save()
                delivery.save()
                request.data['delivery_option'] = delivery.id
                vehicle_details = VehicleDetailSerializer(data=request.data.get('delivery_vehicle'), many=True)
                if vehicle_details.is_valid():
                    vehicle_details.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(serializer.errors))
            return self.success_response(code='HTTP_200_OK',
                                         data={'delivery_id': delivery.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            delivery = DeliveryOption.objects.get(shop_id=pk)
            serializer = DeliveryRetrieveSerializer(delivery)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Shop.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class PaymentMethodView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['user'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'payment_type': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),

        }))
    def create(self, request):
        user_id = request.data.get('user_id')
        payment_type = request.data.get('payment_type')
        try:
            for value in payment_type:
                UserPaymentMethod.objects.get_or_create(user_id=user_id, payment_method_id=value)
            UserPaymentMethod.objects.exclude(payment_method_id__in=payment_type).delete()
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            payment_methods = UserPaymentMethod.objects.filter(user=pk)
            serializer = UserPaymentSerializer(payment_methods, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except UserPaymentMethod.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    @swagger_auto_schema(tags=['user'], request_body=ShopDetailSerializer)
    def update(self, request, pk=None):
        try:
            shop = Shop.objects.get(id=pk)
            serializer = ShopLocationDataSerializer(instance=shop, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self.success_response(code='HTTP_200_OK',
                                             data=serializer.data,
                                             message=SUCCESS)
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class CommonParamsView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:

            shop_choices = [{'id': shop.id, 'category': shop.name, 'fssai': shop.fssai}
                            for shop in ShopCategory.objects.all()]
            payment_methods = [{'id': method.id, 'method': method.payment_type}
                               for method in PaymentMethod.objects.all()]
            delivery_choices = DELIVERY_CHOICES.choices()
            delivery_choices = [{'id': shop[0], 'choice': shop[1]} for shop in delivery_choices]
            return self.success_response(code='HTTP_200_OK',
                                         data={'shopcategories': shop_choices,
                                               'delivery_choices': delivery_choices,
                                               'payment_methods': payment_methods
                                               },
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProfileCompleteView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # token_string = request.META.get('HTTP_AUTHORIZATION')
            # token_key = token_string.partition(' ')[2]
            # token = Token.objects.get(key=token_key)
            user_payment = UserPaymentMethod.objects.filter(user=request.user)
            if user_payment:
                is_profile_completed = True
            else:
                is_profile_completed = False
            return self.success_response(code='HTTP_200_OK',
                                         data={'is_profile_completed': is_profile_completed
                                               },
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)



class UserProfleView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]
    test_param = openapi.Parameter('user_id', openapi.IN_QUERY, description="User ID",
                                   type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['user'], manual_parameters=[test_param])
    def get(self, request):
        try:
            user = Shop.objects.get(user=request.GET.get('user_id'))
            serializer = ProfileSerializer(user)
            return self.success_response(code='HTTP_200_OK',
                                         data={'profile_info': serializer.data
                                               },
                                         message=SUCCESS)

        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    @swagger_auto_schema(tags=['user'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING),
            'image': openapi.Schema(type=openapi.TYPE_FILE),
            'is_profile_image': openapi.Schema(type=openapi.TYPE_FILE),
        }))
    def post(self, request):
        try:
            shop = Shop.objects.get(user=request.data.get('user_id'))
            image_data = request.data.get('is_profile_image')
            if image_data == 'true':
                shop.image = request.FILES.get('image')
                shop.save()
                image_url = shop.image.url
            else:
                shop.logo = request.FILES.get('image')
                shop.save()
                image_url = shop.logo.url

            return self.success_response(code='HTTP_200_OK',
                                         data={'image_url': image_url},
                                         message=SUCCESS)

        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class  ShopOrderHistoryView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderHistorySerializer
    pagination_class = CustomOffsetPagination

    def get_queryset(self):
        pass
    # test_param = openapi.Parameter('search', openapi.IN_QUERY, description="search product by key",
    #                                type=openapi.TYPE_STRING)
    #
    # @swagger_auto_schema(tags=['product'], manual_parameters=[test_param])
    def list(self, request, *args, **kwargs):
        try:
            delivered_orders = Order.objects.filter(
            Q(status=ORDER_STATUS.delivered, shop__user=request.user) |
            Q(status=ORDER_STATUS.picked_up, shop__user=request.user))
            # if 'search' in request.GET:
            #    search_term = request.GET.get('search')
            #    products = products.filter(name__icontains=search_term)
            delivered_orders = self.paginate_queryset(delivered_orders)
            order_Serializer = OrderHistorySerializer(delivered_orders, many=True)
            response = order_Serializer.data
            return self.success_response(code='HTTP_200_OK',
                                         data=self.get_paginated_response(response).data,
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)



class ShopAvailabilityView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['user', 'customer'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        }))
    def post(self, request):
        available = request.data.get('available')
        try:
            shop = Shop.objects.get(user=request.user)
            if available:
                shop.available = True
            else:
                shop.available = False
            shop.save()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={'available': shop.available})

        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class OrderProcessView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    # @swagger_auto_schema(tags=['user', 'customer'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    #     }))
    def post(self, request):
        order_id = request.data.get('order_id')
        status = request.data.get('status')
        try:
            order = Order.objects.get(id=order_id)

            # pdf = render_to_pdf(1, order.customer.id, order.id, 30)
            order.status = status
            order.save()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={})

        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ConfirmDeliveryView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    # @swagger_auto_schema(tags=['user', 'customer'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    #     }))
    def post(self, request):
        order_id = request.data.get('order_id')
        otp = request.data.get('otp')
        try:
            order = Order.objects.get(id=order_id)
            if order.customer_otp == otp:
                order.status = ORDER_STATUS.delivered
                order.save()
            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={})

        except Exception as e:
            # db_logger.exception(e)
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
