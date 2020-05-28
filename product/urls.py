from django.urls import path
from product.views import *

urlpatterns = [
    path('', ProductView.as_view()),
]
