from django.contrib import admin

from product.models import Product, Category


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'size', 'mrp', 'status')


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
