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
    PaymentMethod, UserPaymentMethod, DeliveryOption, DeliveryVehicle

from user.serializers import AccountSerializer, ShopDetailSerializer, ShopLocationDataSerializer, ProfileSerializer,\
    DeliveryDetailSerializer, VehicleDetailSerializer


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



class DeliveryOptionView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['user'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'shop': openapi.Schema(type=openapi.TYPE_INTEGER),
            'delivery_type': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
            'delivery_radius': openapi.Schema(type=openapi.TYPE_STRING),
            'delivery_charge': openapi.Schema(type=openapi.TYPE_NUMBER),
            'vehicle_and_capacity': openapi.Schema(type=openapi.TYPE_STRING),
            'within_km': openapi.Schema(type=openapi.TYPE_STRING),
            'min_charge': openapi.Schema(type=openapi.TYPE_STRING),
            'extra_charge_per_km': openapi.Schema(type=openapi.TYPE_STRING),
        }))
    def post(self, request):
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
                vehicle_details = VehicleDetailSerializer(data=request.data)
                vehicle_details.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(serializer.errors))
            return self.success_response(code='HTTP_200_OK',
                                         data={'delivery_id': delivery.id},
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
            shop_choices = [{'id': shop.id, 'category': shop.name, 'fssai': shop.fssai} for shop in ShopCategory.objects.all()]
            payment_methods = [{'id': method.id, 'method': method.payment_type} for method in PaymentMethod.objects.all()]
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
        }))
    def post(self, request):
        try:
            shop = Shop.objects.get(user=request.data.get('user_id'))
            shop.image = request.FILES.get('image')
            shop.save()
            return self.success_response(code='HTTP_200_OK',
                                         data={'image_url': shop.image.url},
                                         message=SUCCESS)

        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
