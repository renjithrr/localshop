import logging
from django.contrib.auth import authenticate
from django.forms import modelformset_factory

from rest_framework.views import APIView
from rest_framework. viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from utilities.mixins import ResponseViewMixin
from utilities.pagination import CustomOffsetPagination
from utilities.messages import GENERAL_ERROR, DATA_SAVED_SUCCESSFULLY
from product.serializers import ProductSerializer, ProductPricingSerializer, ProductListingSerializer,\
    ProductVarientSerializer
from product.models import Product, ProductVarientImage, ProductVarient
from product.forms import VarientImageForm


class ProductView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=ProductSerializer)
    def post(self, request):
        try:
            try:
                product = Product.objects.get(name=request.data.get('name'))
                serializer = ProductSerializer(instance=product, data=request.data)
            except Product.DoesNotExist:
                serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save()
                # shop.gst_image = request.FILES['gst_image']
                product.save()

            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         data={'product_id': product.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            logging.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)



class ProductPricingView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=ProductPricingSerializer)
    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            serializer = ProductPricingSerializer(instance=product, data=request.data)
            if serializer.is_valid():
                serializer.save()

            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class  ProductListingView(GenericViewSet, ResponseViewMixin):
    permission_classes = [AllowAny]
    serializer_class = ProductListingSerializer
    pagination_class = CustomOffsetPagination
    test_param = openapi.Parameter('search', openapi.IN_QUERY, description="search product by key",
                                   type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['product'], manual_parameters=[test_param])
    def list(self, request, *args, **kwargs):
        try:
            products = Product.objects.all()
            if 'search' in request.GET:
               search_term = request.GET.get('search')
               products = products.filter(name__icontains=search_term)
            paginted_products = self.paginate_queryset(products)
            product_Serializer = ProductListingSerializer(paginted_products, many=True)
            response = product_Serializer.data
            return self.get_paginated_response(response)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductVarientView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=ProductVarientSerializer)
    def post(self, request):
        product_id = request.data.get('product')
        try:
            try:
                varient = ProductVarient.objects.get(product=product_id, size=request.data.get('size'),
                                                     brand=request.data.get('brand'), mrp=request.data.get('mrp'))
                serializer = ProductVarientSerializer(instance=varient, data=request.data)
            except ProductVarient.DoesNotExist:

                serializer = ProductVarientSerializer(data=request.data)
            if serializer.is_valid():
                varient = serializer.save()
                # ImageFormSet = modelformset_factory(ProductVarientImage,
                #                                     form=VarientImageForm, extra=3)
                # formset = ImageFormSet(request.POST, request.FILES,
                #                        queryset=ProductVarientImage.objects.none())
                # for form in fo    rmset.cleaned_data:
                #     # this helps to not crash if the user
                #     # do not upload all the photos
                #     if form:
                #         image = form['image']
                #         photo = ProductVarientImage(varient=varient, image=image)
                #         photo.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
