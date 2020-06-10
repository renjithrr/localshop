from django.contrib import admin

from product.models import Product, Category, Brand, ProductVarient


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'size', 'mrp', 'status')


class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')


class ProductVarientAdmin(admin.ModelAdmin):
    list_display = ('product', 'brand', 'size', 'mrp', 'tax_rate')

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(ProductVarient, ProductVarientAdmin)
