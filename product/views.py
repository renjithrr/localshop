import logging
import io
import csv
import json
from datetime import date, timedelta, datetime
from django.contrib.auth import authenticate
from django.forms import modelformset_factory
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework. viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from utilities.mixins import ResponseViewMixin
from utilities.pagination import CustomOffsetPagination
from utilities.messages import GENERAL_ERROR, DATA_SAVED_SUCCESSFULLY, NOT_A_CSV_FORMAT, SUCCESS
from utilities.utils import BulkCreateManager
from product.serializers import ProductSerializer, ProductPricingSerializer, ProductListingSerializer,\
    ProductVarientSerializer, OrderSerializer
from product.models import Product, ProductVarientImage, ProductVarient, Category, UNIT_CHOICES, COLOR_CHOICES,\
    OrderItem, Order, ORDER_STATUS, PAYMENT_STATUS
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



# class ProductPricingView(APIView, ResponseViewMixin):
#     permission_classes = [IsAuthenticated]
#
#     @swagger_auto_schema(tags=['product'], request_body=ProductPricingSerializer)
#     def post(self, request):
#         product_id = request.data.get('product_id')
#         try:
#             product = Product.objects.get(id=product_id)
#             serializer = ProductPricingSerializer(instance=product, data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#
#             else:
#                 return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
#             return self.success_response(code='HTTP_200_OK',
#                                          message=DATA_SAVED_SUCCESSFULLY)
#         except Exception as e:
#             print(e)
#             return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class  ProductListingView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
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
            return self.success_response(code='HTTP_200_OK',
                                         data=self.get_paginated_response(response).data,
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            product = Product.objects.get(id=pk)
            serializer = ProductSerializer(product)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Product.DoesNotExist:
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
                print(varient)
                serializer = ProductVarientSerializer(instance=varient, data=request.data)
            except ProductVarient.DoesNotExist:
                print("here")
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
                print(serializer.errors)
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductDataCsvView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=ProductVarientSerializer)
    def post(self, request):
        print(request.FILES)
        csv_file = request.FILES['file']
        try:
            if not csv_file.name.endswith('.csv'):
                return self.error_response(code='HTTP_400_BAD_REQUEST', message=NOT_A_CSV_FORMAT)
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)
            bulk_mgr = BulkCreateManager(chunk_size=20)
            for row in csv.reader(io_string, delimiter=',', quotechar="|"):
                # print(row[0])
                category = Category.objects.filter(name__icontains=row[1]).last()

                try:
                    Product.objects.get(hsn_code=row[11])
                except Product.DoesNotExist:
                    bulk_mgr.add(Product(name=row[0], category=category,
                                         size=row[2], color=row[3], quantity=row[4],description=row[5],
                                         brand=row[6], mrp=row[7], offer_prize=row[8], lowest_selling_rate=row[9],
                                         highest_selling_rate=row[10], hsn_code=row[11],
                                         tax_rate=row[12], moq=row[13], unit=row[14]))
            bulk_mgr.done()
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductParamsvView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            category_choices = [{'id': shop.id, 'category': shop.name} for shop in Category.objects.all()]
            color_choices = COLOR_CHOICES.choices()
            unit_choices = UNIT_CHOICES.choices()
            unit_choices = [{'id': unit[0], 'choice': unit[1]} for unit in unit_choices]
            color_choices = [{'id': color[0], 'choice': color[1]} for color in color_choices]

            return self.success_response(code='HTTP_200_OK',
                                         data={'product_categories': category_choices,
                                               'color_choices': color_choices,
                                               'unit_choices': unit_choices
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class SalesView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            todays_sale = Order.objects.filter(payment_status=PAYMENT_STATUS.completed,
                                               created_at__date=date.today()).aggregate(Sum('grand_total'))
            yesterday = date.today() - timedelta(days=1)
            last_7_days = date.today() - timedelta(days=7)
            last_7_days = Order.objects.filter(payment_status=PAYMENT_STATUS.completed,
                                               created_at__date__range=(last_7_days, yesterday)).aggregate(Sum('grand_total'))
            last_31_days = date.today() - timedelta(days=31)
            last_31_days = Order.objects.filter(payment_status=PAYMENT_STATUS.completed,
                                                created_at__date__range=(last_31_days, yesterday)).aggregate(Sum('grand_total'))
            pending_orders = OrderItem.objects.filter(order_id__status=ORDER_STATUS.pending)
            pending_order_serializer = OrderSerializer(pending_orders, many=True)
            accepted_orders = OrderItem.objects.filter(order_id__status=ORDER_STATUS.accepted)
            accepted_order_serializer = OrderSerializer(accepted_orders, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data={'todays_sale': todays_sale['grand_total__sum'],
                                               'last_7_days': last_7_days['grand_total__sum'],
                                               'last_31_days': last_31_days['grand_total__sum'],
                                               'pending_orders': pending_order_serializer.data,
                                               'accepted_orders': accepted_order_serializer.data},
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
