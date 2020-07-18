from django.contrib import admin
from customer.models import Customer, Address


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')


class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'pincode', 'lat', 'long', 'locality')


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Address, AddressAdmin)
