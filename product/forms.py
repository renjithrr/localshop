from django import forms
from product.models import ProductVarientImage


class VarientImageForm(forms.ModelForm):
    image = forms.ImageField(label='Image')
    class Meta:
        model = ProductVarientImage
        fields = ('image', )
