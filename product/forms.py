from django import forms
from product.models import ProductVarientImage, ProductImage
from multiupload.fields import MultiFileField


class VarientImageForm(forms.ModelForm):
    image = forms.ImageField(label='Image')
    class Meta:
        model = ProductVarientImage
        fields = ('image', )


class PhotoForm(forms.ModelForm):
    image = forms.ImageField(label='Image')
    class Meta:
        model = ProductImage
        fields = ('image', )
