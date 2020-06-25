from django.urls import path
from product.views import *
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'listing', ProductListingView, basename='product')


product_list = ProductListingView.as_view({'get': 'list'})
product_detail = ProductListingView.as_view({'get': 'retrieve'})


urlpatterns = [
    path('', ProductView.as_view()),
    # path('pricing', ProductPricingView.as_view()),
    # path('listing', ProductListingView.as_view({'get': 'list'})),
    path('varient', ProductVarientView.as_view()),
    path('upload-product-csv', ProductDataCsvView.as_view()),
    path('product-params', ProductParamsvView.as_view()),
    path('sales-page', SalesView.as_view()),
    path('pending-orders', PendingOrderView.as_view({'get': 'list'})),
    path('accepted-orders', AcceptedOrderView.as_view({'get': 'list'})),
]
urlpatterns += router.urls