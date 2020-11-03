import logging
import io
import csv

from datetime import date, timedelta
from django.db.models import Sum
from django.db.models import Q

from rest_framework.parsers import MultiPartParser, FileUploadParser

from rest_framework.views import APIView
from rest_framework. viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from utilities.mixins import ResponseViewMixin
from utilities.pagination import CustomOffsetPagination
from utilities.messages import GENERAL_ERROR, DATA_SAVED_SUCCESSFULLY, NOT_A_CSV_FORMAT, SUCCESS, PRODUCT_CODE_EXISTS,\
    INVALID_OTP
from utilities.utils import BulkCreateManager, export_to_csv, id_generator, OTPgenerator
from product.serializers import ProductSerializer, ProductPricingSerializer, ProductListingSerializer,\
    ProductVarientSerializer, OrderSerializer, OrderDetailSerializer, ProductRetrieveSerializer
from product.models import Product, ProductVarient, Category, UNIT_CHOICES,\
    ORDER_STATUS, PAYMENT_STATUS, ProductImage, ProductVarientImage
from customer.models import Order, OrderItem, DELIVERY_CHOICES
from user.models import Shop
from user.serializers import ProfileSerializer
from user.tasks import manage_product_quantity, delivery_system_call, render_to_pdf

db_logger = logging.getLogger('db')


class ProductView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=ProductSerializer)
    def post(self, request):
        try:
            try:
                product = Product.objects.get(id=request.data.get('id'))
                serializer = ProductSerializer(instance=product, data=request.data)
            except Product.DoesNotExist:
                try:
                    if request.data.get('product_id'):
                        product = Product.objects.get(product_id=request.data.get('product_id'))
                        if product:
                            return self.error_response(code='HTTP_400_BAD_REQUEST', message=PRODUCT_CODE_EXISTS)
                except Exception as e:
                    db_logger.exception(e)
                    pass
                serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save()
                if request.data.get('image_ids', ''):
                    existing_images = ProductImage.objects.filter(product=product)
                    existing_images = existing_images.exclude(id__in=request.data.get('image_ids', ''))
                    if existing_images:
                        existing_images.delete()
                    for value in request.data.get('image_ids'):
                        try:
                            image = ProductImage.objects.get(id=value)
                            image.product = product
                            image.save()
                        except Exception as e:
                            db_logger.exception(e)
                            pass
                try:
                    if not request.data.get('product_id'):
                        product_id = id_generator()
                        product.product_id = product_id
                        product.save()
                except Exception as e:
                    db_logger.exception(e)
                    pass

                try:
                    shop = Shop.objects.get(user=request.user)
                    product.shop = shop
                    product.save()
                except Exception as e:
                    db_logger.exception(e)
                    pass

            else:
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=str(serializer.errors))
            return self.success_response(code='HTTP_200_OK',
                                         data={'product_id': product.id},
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            db_logger.exception(e)
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
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class  ProductListingView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
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
            products = Product.objects.filter(is_deleted=False, is_hidden=False,
                                              shop__user=request.user).order_by('quantity')
            if 'search' in request.GET:
               search_term = request.GET.get('search')
               products = products.filter(name__icontains=search_term)
            if 'hidden' in request.GET:
                products = Product.objects.filter(is_deleted=False, is_hidden=True,
                                                  shop__user=request.user).order_by('quantity')
            if 'out_of_stock' in request.GET:
                products = products.filter(quantity=0)
            paginted_products = self.paginate_queryset(products)
            product_Serializer = ProductListingSerializer(paginted_products, many=True)
            response = product_Serializer.data
            return self.success_response(code='HTTP_200_OK',
                                         data=self.get_paginated_response(response).data,
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    def retrieve(self, request, pk=None):
        try:
            product = Product.objects.get(id=pk)
            serializer = ProductRetrieveSerializer(product)
            return self.success_response(code='HTTP_200_OK',
                                         data=serializer.data,
                                         message=SUCCESS)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductVarientView(GenericViewSet, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
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
                try:
                    shop = Shop.objects.get(user=request.user)
                    varient.shop = shop
                    varient.save()
                except Exception as e:
                    db_logger.exception(e)
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
                        db_logger.exception(e)
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

    @swagger_auto_schema(tags=['product'], request_body=ProductVarientSerializer)
    def update(self, request, pk=None):
        try:
            if request.data.get('delete'):
                product = Product.objects.get(id=pk)
                product.is_deleted = True
                product.save()
            elif 'hide' in request.data:
                product = Product.objects.get(id=pk)
                if request.data.get('hide'):
                    product.is_hidden = True
                else:
                    product.is_hidden = False
                product.save()
            else:
                try:
                    varient = ProductVarient.objects.get(id=pk)
                    serializer = ProductVarientSerializer(instance=varient, data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        if request.data.get('image_ids', ''):
                            existing_images = ProductVarientImage.objects.exclude(id__in=request.data.get('image_ids', ''))
                            if existing_images:
                                existing_images.delete()
                            for value in request.data.get('image_ids'):
                                try:
                                    image = ProductVarientImage.objects.get(id=value)
                                    image.varient = varient
                                    image.save()
                                except Exception as e:
                                    db_logger.exception(e)
                        return self.success_response(code='HTTP_200_OK',
                                                         data=serializer.data,
                                                         message=SUCCESS)
                    else:
                        return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

                except Exception as e:
                    db_logger.exception(e)
                    return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)
            return self.success_response(code='HTTP_200_OK',
                                         data={},
                                         message=SUCCESS)
        except Exception as e:
            print(e)
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductDataCsvView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

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
                print(row)
                category = Category.objects.filter(name__icontains=row[2]).last()
                existing_product = Product.objects.filter(product_id=row[0])
                if existing_product:
                    update_values = {'name': row[1], 'category': category, 'size': row[3], 'color': row[4],
                                     'quantity': row[5], 'description': row[6], 'brand': row[7], 'mrp': row[8]
                        ,'hsn_code': row[12], 'tax_rate': row[13],
                                     'moq': row[14], 'unit': row[15]
                                     }
                    if row[9]:
                        update_values['offer_prize'] = row[9]
                    if row[10]:
                        update_values['lowest_selling_rate'] = row[10]
                    if row[11]:
                        update_values['highest_selling_rate'] = row[11]


                    existing_product.update(**update_values)

                else:
                    product_id = row[0]
                    try:
                        if not product_id:
                            product_id = id_generator()
                    except Exception as e:
                        db_logger.exception(e)
                    shop = Shop.objects.filter(user=request.user).last()
                    product = Product(name=row[1], category=category,
                                         size=row[3], color=row[4], quantity=row[5],description=row[6],
                                         brand=row[7], mrp=row[8]
                                      , hsn_code=row[12], product_id=product_id,
                                         tax_rate=row[13], moq=row[14], unit=row[15], shop=shop)
                    if row[9]:
                        product.offer_prize = row[9]
                    if row[10]:
                        product.lowest_selling_rate = row[10]
                    if row[11]:
                        product.highest_selling_rate = row[11]


                    bulk_mgr.add(product)
            bulk_mgr.done()
            return self.success_response(code='HTTP_200_OK',
                                         message=DATA_SAVED_SUCCESSFULLY)
        except Exception as e:
            print(e)
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class DownloadProductDataCsvView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    is_sample = openapi.Parameter('is_sample', openapi.IN_QUERY, description="Sample CSV for vendors",
                                   type=openapi.TYPE_BOOLEAN)
    @swagger_auto_schema(tags=['product'], manual_parameters=[is_sample])
    def get(self, request):
        try:
            sample = request.GET.get('is_sample')
            shop = Shop.objects.filter(user=request.user).last()
            return export_to_csv(shop, sample)

        except Exception as e:

            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class ProductParamsvView(APIView, ResponseViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            shop = Shop.objects.filter(user=request.GET.get('user_id')).last()
            shop_category = shop.shop_category
            category_choices = [{'id': shop.id, 'category': shop.name} for shop in Category.objects.
                filter(shop_category=shop_category).order_by('id')]
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
            db_logger.exception(e)
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
                todays_sale = Order.objects.filter(payment_status=PAYMENT_STATUS.completed, shop__user=request.user,
                                                   created_at__date=date.today()).aggregate(Sum('grand_total'))
                yesterday = date.today() - timedelta(days=1)
                last_7_days = date.today() - timedelta(days=7)
                last_7_days = Order.objects.filter(payment_status=PAYMENT_STATUS.completed, shop__user=request.user,
                                                   created_at__date__range=(last_7_days, yesterday)).aggregate(
                    Sum('grand_total'))
                last_31_days = date.today() - timedelta(days=31)
                last_31_days = Order.objects.filter(payment_status=PAYMENT_STATUS.completed, shop__user=request.user,
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
                db_logger.exception(e)
                return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


        except Exception as e:
            db_logger.exception(e)
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
            pending_orders = Order.objects.filter(status=ORDER_STATUS.pending, shop__user=request.user).order_by('id')
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
            db_logger.exception(e)
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

            accepted_orders = Order.objects.filter(Q(status=ORDER_STATUS.accepted) | Q(status=ORDER_STATUS.ready_for_pickup),
                                                   shop__user=request.user).order_by('id')
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
            db_logger.exception(e)
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
            # vendor_otp = None
            order = Order.objects.get(id=request.data.get('order_id'))
            status = request.data.get('status')
            if status == ORDER_STATUS.accepted:
                vendor_otp = OTPgenerator()
                order.otp = vendor_otp
                customer_otp = OTPgenerator()
                order.customer_otp = customer_otp
                manage_product_quantity.apply_async(queue='normal', args=(order.id,))
                if order.delivery_type == DELIVERY_CHOICES.townie_ship:
                    try:
                        customer_address = order.customer.customer_addresses.last()

                        data = {
                            "order_id": str(order.id),
                            "lat": float(customer_address.lat),
                            "long": float(customer_address.long)
                        }
                        delivery_system_call.apply_async(queue='normal', args=(),
                                                         kwargs=data)
                        render_to_pdf.apply_async(queue='normal', args=(order.delivery_type,
                                                                        order.customer.id,
                                                                        order.id,
                                                                        order.delivery_charge))
                        # delivery_system_call(data)
                        # response = requests.post('http://18.222.159.212:8080/v1/assignorder', data=json.dumps(data),
                        #                          headers = {'content-type': 'application/json'})
                        # print(response.text)
                    except Exception as e:
                        db_logger.exception(e)
            elif status == ORDER_STATUS.picked_up:
                otp = request.data.get('otp')
                if order.otp != otp:
                    return self.success_response(code='HTTP_400_BAD_REQUEST',
                                                 data={},
                                                 message=INVALID_OTP)
            elif status == ORDER_STATUS.delivered:
                otp = request.data.get('otp')
                if order.customer_otp != otp:
                    return self.success_response(code='HTTP_400_BAD_REQUEST',
                                                 data={},
                                                 message=INVALID_OTP)
            order.status = status
            order.save()
            # if order.delivery_type == DELIVERY_CHOICES.pickup:
            #     vendor_otp = vendor_otp
            return self.success_response(code='HTTP_200_OK',
                                         message=SUCCESS,
                                         data={'otp': order.otp})
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


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
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)

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
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


class  RateProductView(APIView, ResponseViewMixin):
    permission_classes = [IsAuthenticated]
    #
    # @swagger_auto_schema(tags=['product'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'order_id': openapi.Schema(type=openapi.TYPE_STRING),
    #         'status': openapi.Schema(type=openapi.TYPE_INTEGER),
    #     }))
    def post(self, request, *args, **kwargs):
        try:
            product = Product.objects.get(id=request.data.get('product_id'))
            rating = request.data.get('rating')
            product.rating = rating
            product.save()
            return self.success_response(code='HTTP_200_OK',
                                         message=SUCCESS,
                                         data={})
        except Exception as e:
            db_logger.exception(e)
            return self.error_response(code='HTTP_500_INTERNAL_SERVER_ERROR', message=GENERAL_ERROR)


