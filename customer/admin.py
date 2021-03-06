from django.contrib import admin
from customer.models import Customer, Address, Order, OrderItem, CustomerFavouriteProduct, Invoice


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')


class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'pincode', 'lat', 'long', 'locality')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('grand_total', 'discount', 'payment_status', 'status', 'shop')


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'product_id', 'quantity', 'rate', 'total')

class CustomerFavouriteProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'product')


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice_id', 'order', 'shop')


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(CustomerFavouriteProduct, CustomerFavouriteProductAdmin)
admin.site.register(Invoice, InvoiceAdmin)


