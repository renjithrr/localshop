import logging
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from utilities.mixins import ResponseViewMixin
from utilities.messages import SUCCESS, GENERAL_ERROR
from utilities.utils import id_generator
from customer.models import Order, Shop
from user.models import Shop
from admin.serializers import AdminOrderSerializer, OrderDetailsSerializer, AdminShopSerializer, ShopDetailsSerializer, ProductsSerializer
from user.models import AppUser,USER_TYPE_CHOICES
from customer.models import Customer
from product.models import Product

from rest_framework.authtoken.models import Token


import datetime

db_logger = logging.getLogger('db')


class AdminOrderView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            orders = Order.objects.all().order_by('status')
            serializer = AdminOrderSerializer(orders, many=True)

            return self.success_response(code='HTTP_200_OK',
                                         data={'orders': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class OrderDetailsView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            order_id = request.GET.get('id', '')
            order = Order.objects.get(id=order_id)
            serializer = OrderDetailsSerializer(order)

            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class AdminShopView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            shops = Shop.objects.all().order_by('shop_name')
            serializer = AdminShopSerializer(shops, many=True)

            return self.success_response(code='HTTP_200_OK',
                                         data={'orders': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

class AdminShopSearchView(APIView,ResponseViewMixin):
    permission_classes = [AllowAny]

    def post(self,request):
        try:
            start_date = datetime.datetime.fromtimestamp(request.data.get('start_time'))
            end_date = datetime.datetime.fromtimestamp(request.data.get('end_time'))
            orders = Order.objects.filter(id=request.data.get('id'), created_at__range=(start_date, end_date)).order_by('status')
            serializer = AdminOrderSerializer(orders, many=True)

            return self.success_response(code='HTTP_200_OK',
                                         data={'orders': serializer.data,
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class AdminShopDetailsView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            shop_id = request.GET.get('id', '')
            shop = Shop.objects.get(id=shop_id)
            serializer = ShopDetailsSerializer(shop)

            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

class AdminShopStatusView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            status = request.data.get('status')
            shop_id = request.data.get('shop_id')
            print(shop_id,status)
            try:
                shop = Shop.objects.get(id=shop_id)
                shop.status = status
                shop.save()
            except Shop.DoesNotExist:
                return self.error_response(code='HTTP_404_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

        except Exception as e:
            print(str(e))
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

        return self.success_response(code='HTTP_200_OK', message=SUCCESS)


class AdminSignup(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        try:
            role = USER_TYPE_CHOICES.admin
            try:
                user = AppUser.objects.get(mobile_number=mobile_number)

            except AppUser.DoesNotExist:
                username = id_generator()
                user = AppUser(email=request.data.get('email'), first_name=request.data.get('name'), username=username,
                               mobile_number=mobile_number, role=role)
                user.save()
                Customer.objects.get_or_create(user=user)
            if request.data.get('password') == 'localshop@123':
                token, _ = Token.objects.get_or_create(user=user)
                user.is_active = True
                user.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message='user does not exist')

            return self.success_response(code='HTTP_200_OK', message=SUCCESS,
                                         data={'user_id': user.id,
                                               'user_type': user.role,
                                               'token':token.key
                                               })
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class AdminProductsView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            shop_id = request.GET.get('shop_id', '')
            products = Product.objects.filter(shop_id=shop_id)
            serializer = ProductsSerializer(products, many=True)

            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)