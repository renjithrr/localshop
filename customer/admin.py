from django.contrib import admin
from customer.models import Customer, Address, Order, OrderItem


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')


class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'pincode', 'lat', 'long', 'locality')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('total_amount', 'discount', 'payment_status', 'status', 'shop')


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'product_id', 'quantity', 'rate', 'total')


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
