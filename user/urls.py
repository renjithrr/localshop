from django.urls import path
from user.views import *

urlpatterns = [
    path('login/', LoginView.as_view()),
    # path('logout/', LogoutView.as_view()),
    path('devices/', DeviceTokenView.as_view()),
]
