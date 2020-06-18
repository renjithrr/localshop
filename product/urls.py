from django.urls import path
from product.views import *

urlpatterns = [
    path('', ProductView.as_view()),
    # path('pricing', ProductPricingView.as_view()),
    path('listing', ProductListingView.as_view({'get': 'list'})),
    path('varient', ProductVarientView.as_view()),
    path('upload-product-csv', ProductDataCsvView.as_view()),
    path('product-params', ProductParamsvView.as_view()),

]
