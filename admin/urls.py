from django.urls import path
from rest_framework.routers import DefaultRouter
from admin.views import AdminOrderView, OrderDetailsView, AdminShopView, AdminShopSearchView, AdminShopDetailsView,\
    AdminShopStatusView, AdminSignup,AdminProductsView, OfferImageView, OfferDetailsView


router = DefaultRouter()



urlpatterns = [
    path('pending-orders', AdminOrderView.as_view()),
    path('order-details', OrderDetailsView.as_view()),
    path('shops', AdminShopView.as_view()),
    path('shops:search', AdminShopSearchView.as_view()),

    path('shops-details/', AdminShopDetailsView.as_view()),
    path('shop-status/', AdminShopStatusView.as_view()),
    path('signup/', AdminSignup.as_view()),
    path('products', AdminProductsView.as_view()),
    path('upload-image', OfferImageView.as_view()),
    path('offer-details', OfferDetailsView.as_view())

]
