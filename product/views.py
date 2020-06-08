import logging
from django.contrib.auth import authenticate
from django.forms import modelformset_factory

from rest_framework.views import APIView
from rest_framework. viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from utilities.mixins import ResponseViewMixin
from utilities.messages import GENERAL_ERROR, DATA_SAVED_SUCCESSFULLY
from product.serializers import ProductSerializer, ProductPricingSerializer, ProductListingSerializer
from product.models import Product, ProductVarientImage
from product.forms import VarientImageForm


class ProductView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=ProductSerializer)
    def post(self, request):
        try:
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save()
                # product.image = request.FILES['image']
                # product.save()
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


class ProductListingView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    # @swagger_auto_schema(tags=['product'], request_body=ProductPricingSerializer)
    def list(self, request):
        try:
            products = Product.objects.all()
            if 'search' in request.GET:
               search_term = request.GET.get('search')
               products = products.objects.filter(name__icontains=search_term)
            paginted_products = self.paginate_queyset(products)
            product_Serializer =ProductListingSerializer(paginted_products, many=True)
            response = product_Serializer.data
            return self.get_paginated_response(response)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductVarientView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=ProductPricingSerializer)
    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            serializer = ProductPricingSerializer(instance=product, data=request.data)
            if serializer.is_valid():
                varient = serializer.save()
                ImageFormSet = modelformset_factory(ProductVarientImage,
                                                    form=VarientImageForm, extra=3)
                formset = ImageFormSet(request.POST, request.FILES,
                                       queryset=ProductVarientImage.objects.none())
                for form in formset.cleaned_data:
                    # this helps to not crash if the user
                    # do not upload all the photos
                    if form:
                        image = form['image']
                        photo = ProductVarientImage(varient=varient, image=image)
                        photo.save()
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
