from django.urls import path
from product.views import *
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'listing', ProductListingView, basename='product')
router.register(r'pending-orders', PendingOrderView, basename='pending-orders')
router.register(r'accepted-orders', AcceptedOrderView, basename='accepted-orders')
router.register(r'varient', ProductVarientView, basename='pending-orders')
router.register(r'pricing', ProductPricingView, basename='product-pricing')

product_list = ProductListingView.as_view({'get': 'list'})
product_detail = ProductListingView.as_view({'get': 'retrieve'})
product_update = ProductListingView.as_view({'put': 'update'})

pending_order_list = PendingOrderView.as_view({'get': 'list'})
pending_order_detail = PendingOrderView.as_view({'get': 'retrieve'})

accepted_order_list = AcceptedOrderView.as_view({'get': 'list'})
accepted_order_detail = AcceptedOrderView.as_view({'get': 'retrieve'})

product_varient_create = ProductVarientView.as_view({'post': 'create'})
product_varient_update = ProductVarientView.as_view({'put': 'update'})


product_pricing_create = ProductPricingView.as_view({'post': 'create'})
product_pricing_retrieve = ProductPricingView.as_view({'put': 'update'})
product_pricing_update = ProductPricingView.as_view({'put': 'update'})

urlpatterns = [
    path('', ProductView.as_view()),
    # path('pricing', ProductPricingView.as_view()),
    # path('listing', ProductListingView.as_view({'get': 'list'})),
    # path('varient', ProductVarientView.as_view()),
    path('upload-product-csv', ProductDataCsvView.as_view()),
    path('product-params', ProductParamsvView.as_view()),
    path('sales-page', SalesView.as_view()),
    # path('pending-orders', PendingOrderView.as_view({'get': 'list'})),
    # path('accepted-orders', AcceptedOrderView.as_view({'get': 'list'})),
    path('accept-reject', OrderAcceptRejectView.as_view()),
    path('upload-image', ProductImageUploadView.as_view()),
    # path('order-pickup', OrderPickUpView.as_view()),
]
urlpatterns += router.urls
