from django.urls import path
from user.views import *

urlpatterns = [
    # path('login/', LoginView.as_view()),
    path('verify-number/', VerifyMobileNumberView.as_view()),
    path('verify-otp/', VerifyMobileOtpView.as_view()),
    path('account-details/', AccountDetailsView.as_view()),
    path('shop-details/', ShopDetailsView.as_view()),
    path('location-info/', LocationDataView.as_view()),
    path('common-params/', CommonParamsView.as_view()),
    path('payment-methods/', PaymentMethodView.as_view()),
    path('is-profile-completed/', ProfileCompleteView.as_view()),
    # path('devices/', DeviceTokenView.as_view()),
]
