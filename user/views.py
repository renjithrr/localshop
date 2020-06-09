import logging
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from twilio.rest import Client

from utilities.mixins import ResponseViewMixin
from utilities.messages import INVALID_CREDENTIALS
from utilities.messages import AUTHENTICATION_SUCCESSFUL, SUCCESS
from utilities.messages import PROVIDE_AUTHENTICATION_CREDENTIALS, GENERAL_ERROR, DATA_SAVED_SUCCESSFULLY, INVALID_OTP
from utilities.utils import OTPgenerator

from user.models import DeviceToken, USER_TYPE_CHOICES, AppUser, Shop, AppConfigData, DELIVERY_CHOICES, ShopCategory,\
    PaymentMethod, UserPaymentMethod

from user.serializers import AccountSerializer, ShopDetailSerializer, ShopLocationDataSerializer


# class DeviceTokenView(APIView, ResponseViewMixin):
#     """
#     register a new device when a user logged into the system
#     """
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         try:
#             device_id = request.data.get('device_id', '')
#             user_id = request.data.get('user_id', '')
#             user_type = request.data.get('user_type', '')
#             obj, _ = DeviceToken.objects.get_or_create(user_id=user_id, user_type=user_type,
#                                                        defaults={'is_active': True})
#             obj.device_id = device_id
#             obj.save()
#
#             return self.success_response(code='HTTP_200_OK')
#         except Exception as e:
#             logging.exception(e)
#             return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


# class LoginView(APIView, ResponseViewMixin):
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         try:
#             serializer = UserSerializer(data=request.data)
#             if serializer.is_valid():
#                 valid_data = serializer.data
#                 username = valid_data.get("username")
#                 password = valid_data.get("password")
#                 if not username or not password:
#                     return self.error_response(code='HTTP_400_BAD_REQUEST',
#                                                message=PROVIDE_AUTHENTICATION_CREDENTIALS)
#                 user = authenticate(username=username, password=password)
#                 token, _ = Token.objects.get_or_create(user=user)
#
#                 return self.success_response(code='HTTP_200_OK', message=AUTHENTICATION_SUCCESSFUL,
#                                              data={'user_id': user.id,
#                                                    'user_type': user.role,
#                                                    'token': token.key
#                                                    })
#             else:
#                 return self.error_response(code='HTTP_400_BAD_REQUEST', message=INVALID_CREDENTIALS)
#         except Exception as e:
#             logging.exception(e)
#             return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=INVALID_CREDENTIALS)


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
                account_sid = AppConfigData.objects.get(key='TWILIO_ACCOUNT_ID').value
                auth_token = AppConfigData.objects.get(key='TWILIO_AUTH_TOKEN').value
                client = Client(account_sid, auth_token)
                otp = OTPgenerator()
                message = client.messages.create(
                    body=otp,
                    from_='+17402791825',
                    to=mobile_number
                )
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
                return self.success_response(code='HTTP_200_OK', message=AUTHENTICATION_SUCCESSFUL,
                                             data={'user_id': user.id,
                                                   'user_type': user.role,
                                                   'token': token.key
                                                   })
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=INVALID_OTP)

        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class AccountDetailsView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['user'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'account_number': openapi.Schema(type=openapi.TYPE_STRING),
            'ifsc_code': openapi.Schema(type=openapi.TYPE_STRING),
            'account_name': openapi.Schema(type=openapi.TYPE_STRING),

        }))
    def post(self, request):
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


class ShopDetailsView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['user'], request_body=ShopDetailSerializer)
    def post(self, request):
        user_id = request.data.get('user')
        try:
            try:
                shop = Shop.objects.get(user=user_id, shop_name=request.data.get('shop_name'))
                serializer = ShopDetailSerializer(instance=shop, data=request.data)
            except Shop.DoesNotExist:
                serializer = ShopDetailSerializer(data=request.data)
            if serializer.is_valid():
                shop = serializer.save()
                # shop.gst_image = request.FILES['gst_image']
                shop.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         data={'shop_id': shop.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            logging.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class LocationDataView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['user'], request_body=ShopLocationDataSerializer())
    def post(self, request):
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


class PaymentMethodView(APIView, ResponseViewMixin):
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


class CommonParamsView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            values = {}
            shop_choices = list(ShopCategory.objects.values_list('id', 'name'))
            payment_methods = PaymentMethod.objects.all()
            for value in payment_methods:
                values.update({value.id: {value.payment_type: value.choices}})

            delivery_choices = DELIVERY_CHOICES.choices()
            return self.success_response(code='HTTP_200_OK',
                                         data={'shopcategories': dict(shop_choices),
                                               'delivery_choices': dict(delivery_choices),
                                               'payment_methods': values
                                               },
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
