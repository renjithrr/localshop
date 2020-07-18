from django.urls import path
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
from customer.views import NearbyShop, CommonParamsView, OrderHistoryView, CustomerAddressView

router.register(r'pricing', CustomerAddressView, basename='product-pricing')

product_list = CustomerAddressView.as_view({'get': 'list'})
product_detail = CustomerAddressView.as_view({'get': 'retrieve'})
product_update = CustomerAddressView.as_view({'post': 'create'})

urlpatterns = [
    path('nearby-shops', NearbyShop.as_view()),
    path('common-params', CommonParamsView.as_view()),
    path('order-history', OrderHistoryView.as_view()),
]
