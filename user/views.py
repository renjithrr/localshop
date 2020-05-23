import logging
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from utilities.mixins import ResponseViewMixin
from utilities.messages import INVALID_CREDENTIALS
from utilities.messages import AUTHENTICATION_SUCCESSFUL
from utilities.messages import PROVIDE_AUTHENTICATION_CREDENTIALS, GENERAL_ERROR

from user.models import DeviceToken, USER_TYPE_CHOICES, AppUser
from user.serializers import UserSerializer


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
                pass
            return self.success_response(code='HTTP_200_OK', message=AUTHENTICATION_SUCCESSFUL,
                                         data={'user_id': user.id,
                                               'user_type': user.role
                                               })
        except Exception as e:
            logging.exception(e)
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
        otp = request.data.get('mobile_number')
        try:
            user = AppUser.objects.get(mobile_number=mobile_number)
            return self.success_response(code='HTTP_200_OK', message=AUTHENTICATION_SUCCESSFUL,
                                         data={'user_id': user.id,
                                               'user_type': user.role
                                               })
        except Exception as e:
            logging.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
