import logging
import io
import csv
import json
from datetime import date, timedelta, datetime
from django.contrib.auth import authenticate
# from django.forms import modelformset_factory
from django.db.models import Sum
from django.db.models import Q
from django.forms.models import modelformset_factory
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser

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
    ProductVarientSerializer, OrderSerializer, OrderDetailSerializer, ProductRetrieveSerializer,\
    ProductUpdateSerializer, ProductImageSerializer
from product.models import Product, ProductVarientImage, ProductVarient, Category, UNIT_CHOICES,\
    OrderItem, Order, ORDER_STATUS, PAYMENT_STATUS, ProductImage, ProductVarientImage
from product.forms import VarientImageForm, PhotoForm
from user.models import Shop
from user.serializers import ProfileSerializer


class ProductView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=ProductSerializer)
    def post(self, request):
        try:
            try:
                product = Product.objects.get(id=request.data.get('id'))
                serializer = ProductSerializer(instance=product, data=request.data)
            except Product.DoesNotExist:
                serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save()
                product.save()
            if request.data.get('image_ids', ''):
                for value in request.data.get('image_ids'):
                    try:
                        image = ProductImage.objects.get(id=value)
                        image.product = product
                        image.save()
                    except Exception as e:
                        pass

            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(serializer.errors))
            return self.success_response(code='HTTP_200_OK',
                                         data={'product_id': product.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            logging.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductImageUploadView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FileUploadParser)
    # @swagger_auto_schema(tags=['product'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'is_product': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    #         'image': openapi.Schema(type=openapi.TYPE_FILE),
    #         'image_id': openapi.Schema(type=openapi.TYPE_NUMBER),
    #     }))
    def post(self, request):
        try:
            from user.models import AppUser
            is_product = request.data.get('is_product')
            image_id = request.data.get('image_id', '')
            images = dict((request.data).lists())['image']
            product_list = []
            if is_product == 'true':
                model = ProductImage
            else:
                model = ProductVarientImage

            if image_id:
                try:
                    photo = model.objects.get(id=image_id)
                    photo.image = request.FILES['image']
                    photo.save()
                    product_list.append({'id': photo.id, 'image_url': photo.image.url})
                except model.DoesNotExist:
                    pass
            else:
                for value in images:
                    photo = model(image=value)
                    photo.save()
                    product_list.append({'id': photo.id, 'image_url': photo.image.url})

            return self.success_response(code='HTTP_200_OK',
                                         data={'image_details': product_list},
                                         message=SUCCESS)

        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class  ProductListingView(GenericViewSet, ResponseViewMixin):
    permission_classes = [AllowAny]
    serializer_class = ProductListingSerializer
    pagination_class = CustomOffsetPagination
    test_param = openapi.Parameter('search', openapi.IN_QUERY, description="search product by key",
                                   type=openapi.TYPE_STRING)
    test_param1 = openapi.Parameter('all', openapi.IN_QUERY, description="List all products",
                                    type=openapi.TYPE_STRING)
    test_param2 = openapi.Parameter('hidden', openapi.IN_QUERY, description="list hidden",
                                    type=openapi.TYPE_STRING)
    test_param3 = openapi.Parameter('out_of_stock', openapi.IN_QUERY, description="List all out of stock products",
                                    type=openapi.TYPE_STRING)

    def get_queryset(self):
        pass
    
    @swagger_auto_schema(tags=['product'], manual_parameters=[test_param, test_param1, test_param2, test_param3])
    def list(self, request, *args, **kwargs):
        try:
            products = Product.objects.filter(is_deleted=False).order_by('quantity')
            if 'search' in request.GET:
               search_term = request.GET.get('search')
               products = products.filter(name__icontains=search_term)
            if 'hidden' in request.GET:
                products = products.filter(is_hidden=True)
            if 'out_of_stock' in request.GET:
                products = products.filter(quantity=0)
            paginted_products = self.paginate_queryset(products)
            product_Serializer = ProductListingSerializer(paginted_products, many=True)
            response = product_Serializer.data
            return self.success_response(code='HTTP_200_OK',
                                         data=self.get_paginated_response(response).data,
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))

    def retrieve(self, request, pk=None):
        try:
            product = Product.objects.get(id=pk)
            serializer = ProductRetrieveSerializer(product)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class ProductVarientView(GenericViewSet, ResponseViewMixin):
    permission_classes = [AllowAny]
    serializer_class = ProductVarientSerializer

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['product'], request_body=ProductVarientSerializer)
    def create(self, request):
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
            if request.data.get('image_ids', ''):
                for value in request.data.get('image_ids'):
                    try:
                        image = ProductVarientImage.objects.get(id=value)
                        image.varient = varient
                        image.save()
                    except Exception as e:
                        pass
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    @swagger_auto_schema(tags=['product'], request_body=ProductVarientSerializer)
    def update(self, request, pk=None):
        try:
            varient = ProductVarient.objects.get(id=pk)
            if request.data.get('delete'):
                varient.is_deleted = True
                varient.save()
            elif request.data.get('hide'):
                varient.is_hidden = True
                varient.save()
            else:
                serializer = ProductVarientSerializer(instance=varient, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return self.success_response(code='HTTP_200_OK',
                                                 data=serializer.data,
                                                 message=SUCCESS)
                else:
                    return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         message=SUCCESS)
        except Exception as e:
            product = Product.objects.get(id=pk)
            if request.data.get('delete'):
                product.is_deleted = True
                product.save()
            elif request.data.get('hide'):
                product.is_hidden = True
                product.save()
            else:
                serializer = ProductUpdateSerializer(instance=product, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return self.success_response(code='HTTP_200_OK',
                                                 data=serializer.data,
                                                 message=SUCCESS)
                else:
                    return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(serializer.errors))

            return self.success_response(code='HTTP_200_OK',
                                         message=SUCCESS)


class ProductDataCsvView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    test_param = openapi.Parameter('file', openapi.IN_QUERY, description="Upload CSV file for product update",
                                   type=openapi.TYPE_FILE)

    @swagger_auto_schema(tags=['product'], manual_parameters=[test_param])
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
                existing_product = Product.objects.filter(hsn_code=row[11])
                if existing_product:
                    update_values = {'name': row[0], 'category': category, 'size': row[2], 'color': row[3],
                                     'quantity': row[4], 'description': row[5], 'brand': row[6], 'mrp': row[7],
                                     'offer_prize': row[8], 'lowest_selling_rate': row[9],
                                     'highest_selling_rate': row[10], 'tax_rate': row[12], 'moq': row[13],
                                     'unit': row[14]
                                     }
                    existing_product.update(**update_values)

                else:
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
            unit_choices = UNIT_CHOICES.choices()
            unit_choices = [{'id': unit[0], 'choice': unit[1]} for unit in unit_choices]
            order_status = ORDER_STATUS.choices()
            order_status = [{'id': unit[0], 'choice': unit[1]} for unit in order_status]
            return self.success_response(code='HTTP_200_OK',
                                         data={'product_categories': category_choices,
                                               'order_status': order_status,
                                               'unit_choices': unit_choices
                                               },
                                         message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class SalesView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    test_param = openapi.Parameter('user_id', openapi.IN_QUERY, description="User ID",
                                   type=openapi.TYPE_STRING)

    @swagger_auto_schema(tags=['product'], manual_parameters=[test_param])
    def get(self, request):
        try:
            try:
                shop = Shop.objects.filter(user=request.GET.get('user_id')).last()
                serializer = ProfileSerializer(shop)
                profile_info = serializer.data
                todays_sale = Order.objects.filter(payment_status=PAYMENT_STATUS.completed,
                                                   created_at__date=date.today()).aggregate(Sum('grand_total'))
                yesterday = date.today() - timedelta(days=1)
                last_7_days = date.today() - timedelta(days=7)
                last_7_days = Order.objects.filter(payment_status=PAYMENT_STATUS.completed,
                                                   created_at__date__range=(last_7_days, yesterday)).aggregate(
                    Sum('grand_total'))
                last_31_days = date.today() - timedelta(days=31)
                last_31_days = Order.objects.filter(payment_status=PAYMENT_STATUS.completed,
                                                    created_at__date__range=(last_31_days, yesterday)).aggregate(
                    Sum('grand_total'))
                # pending_orders = OrderItem.objects.filter(order_id__status=ORDER_STATUS.pending)
                # pending_order_serializer = OrderSerializer(pending_orders, many=True)
                # accepted_orders = OrderItem.objects.filter(order_id__status=ORDER_STATUS.accepted)
                # accepted_order_serializer = OrderSerializer(accepted_orders, many=True)

                return self.success_response(code='HTTP_200_OK',
                                             data={'todays_sale': todays_sale['grand_total__sum'],
                                                   'last_7_days': last_7_days['grand_total__sum'],
                                                   'last_31_days': last_31_days['grand_total__sum'],
                                                   # 'pending_orders': pending_order_serializer.data,
                                                   # 'accepted_orders': accepted_order_serializer.data
                                                   'profile_info': profile_info
                                                   },
                                             message=SUCCESS)
            except Exception as e:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class  PendingOrderView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductListingSerializer
    pagination_class = CustomOffsetPagination

    def get_queryset(self):
        pass
    # test_param = openapi.Parameter('search', openapi.IN_QUERY, description="search product by key",
    #                                type=openapi.TYPE_STRING)
    #
    # @swagger_auto_schema(tags=['product'], manual_parameters=[test_param])
    def list(self, request, *args, **kwargs):
        try:
            pending_orders = Order.objects.filter(status=ORDER_STATUS.pending)
            # if 'search' in request.GET:
            #    search_term = request.GET.get('search')
            #    products = products.filter(name__icontains=search_term)
            pending_orders = self.paginate_queryset(pending_orders)
            order_Serializer = OrderSerializer(pending_orders, many=True)
            response = order_Serializer.data
            return self.success_response(code='HTTP_200_OK',
                                         data=self.get_paginated_response(response).data,
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            order = Order.objects.get(id=pk)
            serializer = OrderDetailSerializer(order)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Product.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

class  AcceptedOrderView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductListingSerializer
    pagination_class = CustomOffsetPagination
    # test_param = openapi.Parameter('search', openapi.IN_QUERY, description="search product by key",
    #                                type=openapi.TYPE_STRING)
    #
    # @swagger_auto_schema(tags=['product'], manual_parameters=[test_param])
    def list(self, request, *args, **kwargs):
        try:

            accepted_orders = Order.objects.filter(Q(status=ORDER_STATUS.accepted) | Q(status=ORDER_STATUS.ready_for_pickup))
            # if 'search' in request.GET:
            #    search_term = request.GET.get('search')
            #    products = products.filter(name__icontains=search_term)
            accepted_orders = self.paginate_queryset(accepted_orders)
            order_Serializer = OrderSerializer(accepted_orders, many=True)
            response = order_Serializer.data
            return self.success_response(code='HTTP_200_OK',
                                         data=self.get_paginated_response(response).data,
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            items = OrderItem.objects.filter(order_id=pk)
            serializer = OrderDetailSerializer(items, many=True)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Product.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

class  OrderAcceptRejectView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'order_id': openapi.Schema(type=openapi.TYPE_STRING),
            'status': openapi.Schema(type=openapi.TYPE_INTEGER),
        }))
    def post(self, request, *args, **kwargs):
        try:
            print(request.data)
            order = Order.objects.get(id=request.data.get('order_id'))
            status = request.data.get('status')
            order.status = status
            order.save()
            return self.success_response(code='HTTP_200_OK',
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))


class  ProductPricingView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductPricingSerializer

    def get_queryset(self):
        pass

    @swagger_auto_schema(tags=['product'], request_body=ProductPricingSerializer)
    def create(self, request, *args, **kwargs):
        try:
            product = Product.objects.get(id=request.data.get('product_id'))
            serializer = ProductPricingSerializer(instance=product, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self.success_response(code='HTTP_200_OK',
                                             message=SUCCESS)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))

    def retrieve(self, request, pk=None):
        try:
            product = Product.objects.get(id=pk)
            serializer = ProductPricingSerializer(product)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Product.DoesNotExist:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    @swagger_auto_schema(tags=['product'], request_body=ProductPricingSerializer)
    def update(self, request, pk=None):
        try:
            product = Product.objects.get(id=pk)
            serializer = ProductPricingSerializer(instance=product, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self.success_response(code='HTTP_200_OK',
                                             data=serializer.data,
                                             message=SUCCESS)
            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
        except Exception as e:
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(e))
