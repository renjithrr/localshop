import logging
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from utilities.mixins import ResponseViewMixin
from utilities.messages import GENERAL_ERROR, DATA_SAVED_SUCCESSFULLY
from product.serializers import ProductSerializer
from product.models import Product


class ProductView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['product'], request_body=ProductSerializer)
    def post(self, request):
        try:
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         data={'product_id': product.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            logging.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
