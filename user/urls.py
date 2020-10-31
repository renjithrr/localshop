from django.urls import path
from user.views import *

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'shop-details', ShopDetailsView, basename='shop-details')
router.register(r'location-info', LocationDataView, basename='location-data')
router.register(r'account-details', AccountDetailsView, basename='account-data')
router.register(r'payment-methods', PaymentMethodView, basename='payment-methods')
router.register(r'delivery-option', DeliveryOptionView, basename='account-data')
router.register(r'order-history', ShopOrderHistoryView, basename='order-history')

pending_order_list = ShopOrderHistoryView.as_view({'get': 'list'})

create_shop_detail = ShopDetailsView.as_view({'post': 'create'})
retrieve_shop_detail = ShopDetailsView.as_view({'get': 'retrieve'})
# update_shop_detail = ShopDetailsView.as_view({'put': 'update'})

create_shop_location = LocationDataView.as_view({'post': 'create'})
retrieve_shop_location = LocationDataView.as_view({'get': 'retrieve'})
# update_shop_location = LocationDataView.as_view({'put': 'update'})

create_account_data = AccountDetailsView.as_view({'post': 'create'})
retrieve_account_data = AccountDetailsView.as_view({'get': 'retrieve'})
# update_account_data = AccountDetailsView.as_view({'put': 'update'})

create_delivery_option = DeliveryOptionView.as_view({'post': 'create'})
retrieve_delivery_option = DeliveryOptionView.as_view({'get': 'retrieve'})
# update_delivery_option = DeliveryOptionView.as_view({'put': 'update'})
create_payment_type = PaymentMethodView.as_view({'post': 'create'})
retrieve_payment_type = PaymentMethodView.as_view({'get': 'retrieve'})
# update_payment_type = PaymentMethodView.as_view({'put': 'update'})

urlpatterns = [
    # path('login/', LoginView.as_view()),
    path('verify-number/', VerifyMobileNumberView.as_view()),
    path('verify-otp/', VerifyMobileOtpView.as_view()),
    # path('account-details/', AccountDetailsView.as_view()),
    # path('shop-details/', ShopDetailsView.as_view()),
    # path('location-info/', LocationDataView.as_view()),
    path('common-params/', CommonParamsView.as_view()),
    # path('payment-methods/', PaymentMethodView.as_view()),
    path('is-profile-completed/', ProfileCompleteView.as_view()),
    path('profile/', UserProfleView.as_view()),
    path('availability/', ShopAvailabilityView.as_view()),
    path('status-change/', OrderProcessView.as_view()),
    path('confirm-delivery/', ConfirmDeliveryView.as_view()),
    # path('delivery-option/', DeliveryOptionView.as_view()),
    # path('devices/', DeviceTokenView.as_view()),
]
urlpatterns += router.urls
