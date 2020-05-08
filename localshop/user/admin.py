from django.contrib import admin
from user.models import AppUser, DeviceToken


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_active')



class DeviceTokenAdmin(admin.ModelAdmin):
    pass


admin.site.register(AppUser, UserAdmin)
admin.site.register(DeviceToken, DeviceTokenAdmin)
