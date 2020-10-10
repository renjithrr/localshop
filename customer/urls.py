from django.urls import path
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
from customer.views import NearbyShop, CommonParamsView, OrderHistoryView, CustomerAddressView, ProductListing, \
    CustomerSignup, AccountEditView, CustomerFavouriteView, ProductVarientView, OrderView, ShopView, BannerView,\
    TrendingShopsView, IsRepeatPossibleView, IsDeliveryAvailableView, IsUnderServiceAreaView, ApplyCouponView,\
    DeliveryChargeView, GenerateTokenView, PaymentUpdateView, GetLocationView, SearchProductView, GetAllLocationView,\
    TrendingOfferView, FavouriteProductView, BargainPriceView

router.register(r'address', CustomerAddressView, basename='product-pricing')

customer_address_list = CustomerAddressView.as_view({'get': 'list'})
customer_address_retrieve = CustomerAddressView.as_view({'get': 'retrieve'})
customer_address_create = CustomerAddressView.as_view({'post': 'create'})
customer_address_delete = CustomerAddressView.as_view({'delete': 'delete'})


urlpatterns = [
    path('nearby-shops', NearbyShop.as_view()),
    path('common-params', CommonParamsView.as_view()),
    path('order-history', OrderHistoryView.as_view()),
    path('products', ProductListing.as_view()),
    path('signup', CustomerSignup.as_view()),
    path('edit-account', AccountEditView.as_view()),
    path('favourite', CustomerFavouriteView.as_view()),
    path('product-varients', ProductVarientView.as_view()),
    path('product-varients', ProductVarientView.as_view()),
    path('order', OrderView.as_view()),
    path('shop', ShopView.as_view()),
    path('banners', BannerView.as_view()),
    path('trending-shops', TrendingShopsView.as_view()),
    path('is-repeat-possible', IsRepeatPossibleView.as_view()),
    path('is-delivery-available', IsDeliveryAvailableView.as_view()),
    path('is-under-service-area', IsUnderServiceAreaView.as_view()),
    path('apply-coupon', ApplyCouponView.as_view()),
    path('delivery-charge', DeliveryChargeView.as_view()),
    path('place-order', GenerateTokenView.as_view()),
    path('payment-update', PaymentUpdateView.as_view()),
    path('location', GetLocationView.as_view()),
    path('search', SearchProductView.as_view()),
    path('all-locations', GetAllLocationView.as_view()),
    path('trending-offers', TrendingOfferView.as_view()),
    path('favourite-products', FavouriteProductView.as_view()),
    path('bargain-price', BargainPriceView.as_view()),



]
urlpatterns += router.urls
