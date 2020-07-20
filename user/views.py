import logging
import boto3
from rest_framework. viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from twilio.rest import Client

from utilities.mixins import ResponseViewMixin
from utilities.messages import AUTHENTICATION_SUCCESSFUL, SUCCESS
from utilities.messages import GENERAL_ERROR, DATA_SAVED_SUCCESSFULLY, INVALID_OTP
from utilities.utils import OTPgenerator

from user.models import USER_TYPE_CHOICES, AppUser, Shop, AppConfigData, DELIVERY_CHOICES, ShopCategory,\
    PaymentMethod, UserPaymentMethod, DeliveryOption

from user.serializers import AccountSerializer, ShopDetailSerializer, ShopLocationDataSerializer, ProfileSerializer,\
    DeliveryDetailSerializer, VehicleDetailSerializer, DeliveryRetrieveSerializer, UserPaymentSerializer


class VerifyMobileNumberView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['user'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
        }))
    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        try:
            user, created = AppUser.objects.get_or_create(
                username=mobile_number,
                mobile_number=mobile_number,
                defaults={'role': USER_TYPE_CHOICES.vendor, 'is_active': False},
            )
            if created:
                aws_access_key_id = AppConfigData.objects.get(key='AWS_ACCESS_KEY_ID').value
                aws_secret_access_key = AppConfigData.objects.get(key='AWS_SECRET_ACCESS_KEY').value
                topic_arn = AppConfigData.objects.get(key='TOPIC_ARN').value
                otp = OTPgenerator()
                client = boto3.client(
                    "sns",
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name="us-east-1"
                )
                client.subscribe(
                    TopicArn=topic_arn,
                    Protocol='sms',
                    Endpoint=mobile_number  # <-- number who'll receive an SMS message.
                )
                client.publish(Message="Townie verification otp is " + otp, TopicArn=topic_arn)
                user.verification_otp = otp
                user.save()
            return self.success_response(code='HTTP_200_OK', message=AUTHENTICATION_SUCCESSFUL,
                                         data={'user_id': user.id,
                                               'user_type': user.role
                                               })
        except Exception as e:
            logging.exception(e)
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class VerifyMobileOtpView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['user'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
            'otp': openapi.Schema(type=openapi.TYPE_STRING),
        }))
    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        otp = request.data.get('otp')
        try:
            user = AppUser.objects.get(mobile_number=mobile_number)
            if user.verification_otp == otp:
                token, _ = Token.objects.get_or_create(user=user)
                user.is_active = True
                user.save()
                try:
                    UserPaymentMethod.objects.get(user=user)
                    is_profile_completed = True
                except UserPaymentMethod.DoesNotExist:
                    is_profile_completed = False
                return self.success_response(code='HTTP_200_OK', message=AUTHENTICATION_SUCCESSFUL,
                                             data={'user_id': user.id,
                                                   'user_type': user.role,
                                                   'token': token.key,
                                                   'is_profile_completed': is_profile_completed
                                                   })
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=INVALID_OTP)

        except Exception as e:
            print(e)
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
            logging.exception(e)
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
        user_id = request.data['data']['user']
        try:

            shop = Shop.objects.filter(user=user_id).first()
            if shop:
                serializer = ShopDetailSerializer(instance=shop, data=request.data['data'])
            else:
                serializer = ShopDetailSerializer(data=request.data['data'])
            if serializer.is_valid():
                shop = serializer.save()
                if request.FILES['gst_image']:
                    shop.gst_image = request.FILES['gst_image']
                shop.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(serializer.errors))
            return self.success_response(code='HTTP_200_OK',
                                         data={'shop_id': shop.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            logging.exception(e)
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
            return self.success_response(code='HTTP_200_OK',
                                         data={'user_id': shop.user.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
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
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))

    def retrieve(self, request, pk=None):
        try:
            delivery = DeliveryOption.objects.get(id=pk)
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
    def post(self, request):
        user_id = request.data.get('user_id')
        payment_type = request.data.get('payment_type')
        try:
            for value in payment_type:
                UserPaymentMethod.objects.get_or_create(user_id=user_id, payment_method_id=value)
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            payment_methods = UserPaymentMethod.objects.filter(user=pk)
            serializer = UserPaymentSerializer(payment_methods, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Shop.DoesNotExist:
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
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


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
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProfileCompleteView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            token_string = request.META.get('HTTP_AUTHORIZATION')
            token_key = token_string.partition(' ')[2]
            token = Token.objects.get(key=token_key)
            user_payment = UserPaymentMethod.objects.filter(user=token.user)
            if user_payment:
                is_profile_completed = True
            else:
                is_profile_completed = False
            return self.success_response(code='HTTP_200_OK',
                                         data={'is_profile_completed': is_profile_completed
                                               },
                                         message=SUCCESS)
        except Exception as e:
            print(e)
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
            print(e)
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
            if request.data.get('is_profile_image'):
                shop.image = request.FILES.get('image')
            else:
                shop.logo = request.FILES.get('image')
            shop.save()
            return self.success_response(code='HTTP_200_OK',
                                         data={'image_url': shop.image.url},
                                         message=SUCCESS)

        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


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
