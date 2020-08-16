from django.urls import path
from rest_framework.routers import DefaultRouter
from admin.views import AdminOrderView, OrderDetailsView, AdminShopView, AdminShopSearchView


router = DefaultRouter()



urlpatterns = [
    path('pending-orders', AdminOrderView.as_view()),
    path('order-details/', OrderDetailsView.as_view()),
    path('shops', AdminShopView.as_view()),
    path('shops:search', AdminShopSearchView.as_view()),


]
