from django.contrib import admin

from product.models import Product, Category, Brand


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'size', 'mrp', 'status')


class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
