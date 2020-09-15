from django.contrib import admin
from django.contrib.gis.geos import Point

from user.models import AppUser, DeviceToken, Shop, AppConfigData, ShopCategory, PaymentMethod, UserPaymentMethod, \
    DeliveryVehicle, DeliveryOption, ServiceArea, Coupon


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_active')



class DeviceTokenAdmin(admin.ModelAdmin):
    pass


class ShopAdmin(admin.ModelAdmin):
    list_display = ('vendor_name', 'user', 'shop_name', 'business_name', 'location')


class AppConfigDataAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')


class ShopCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('payment_type', 'choices')


class UserPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_method')


class DeliveryVehicleAdmin(admin.ModelAdmin):
    list_display = ('delivery_option', 'vehicle_and_capacity', 'min_charge', 'within_km', 'extra_charge_per_km')


class DeliveryOptionAdmin(admin.ModelAdmin):
    list_display = ('shop', 'delivery_type', 'delivery_charge', 'delivery_charge')


class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'lat', 'long')

    def save_model(self, request, obj, form, change):
        longitude = obj.long
        latitude = obj.lat
        location = Point(float(longitude), float(latitude))
        obj.location = location
        super().save_model(request, obj, form, change)

class CouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'discount', 'is_percentage', 'is_active')


admin.site.register(AppUser, UserAdmin)
admin.site.register(DeviceToken, DeviceTokenAdmin)
admin.site.register(Shop, ShopAdmin)
admin.site.register(AppConfigData, AppConfigDataAdmin)
admin.site.register(ShopCategory, ShopCategoryAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(UserPaymentMethod, UserPaymentMethodAdmin)
admin.site.register(DeliveryVehicle, DeliveryVehicleAdmin)
admin.site.register(DeliveryOption, DeliveryOptionAdmin)
admin.site.register(ServiceArea, ServiceAreaAdmin)
admin.site.register(Coupon, CouponAdmin)

