from django.urls import path
from user.views import *

urlpatterns = [
    # path('login/', LoginView.as_view()),
    path('verify-number/', VerifyMobileNumberView.as_view()),
    path('verify-otp/', VerifyMobileOtpView.as_view()),
    path('account-details/', AccountDetailsView.as_view()),
    path('shop-details/', ShopDetailsView.as_view()),
    path('gst-info/', GstDataView.as_view()),
    # path('devices/', DeviceTokenView.as_view()),
]
