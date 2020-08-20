from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from utilities.mixins import ResponseViewMixin
from utilities.messages import SUCCESS, GENERAL_ERROR
from customer.models import Order
from user.models import Shop
from admin.serializers import AdminOrderSerializer, OrderDetailsSerializer, AdminShopSerializer
import datetime



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