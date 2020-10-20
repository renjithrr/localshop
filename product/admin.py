import openpyxl
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from django import forms


from product.models import Product, Category, Brand, ProductVarient, ProductImage, ProductVarientImage


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'shop_category')

class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image',)


class ProductVarientImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image',)


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


class ProductAdmin(admin.ModelAdmin):
    change_list_template = "product_bulk_upload.html"
    #
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-products/', self.import_products),]
        return my_urls + urls

    def import_products(self, request):
        try:
            print(request.method)
            if request.method == "POST":

                csv_file = request.FILES["csv_file"]

                wb = openpyxl.load_workbook(csv_file)
                worksheet = wb.worksheets[0]
                for row_value_list in worksheet.iter_rows():
                    row = [cell.value for cell in row_value_list if cell.row != 1 and cell.value]
                    if row:
                        self.get_row(row, request)
                self.message_user(request, "Your csv file has been imported")
                return redirect("..")
            form = CsvImportForm()
            payload = {"form": form}
            return render(
                request, "csv_form.html", payload
            )
        except Exception as e:
            self.message_user(request, str(e))
            return redirect("..")

    list_display = ('name', 'shop', 'category', 'size', 'mrp', 'status')


class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')


class ProductVarientAdmin(admin.ModelAdmin):
    list_display = ('product', 'brand', 'size', 'mrp', 'tax_rate')



admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(ProductVarient, ProductVarientAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(ProductVarientImage, ProductVarientImageAdmin)
