from django import forms
from .models import ShippingDetail

class ShippingForm(forms.ModelForm):
    class Meta:
        model = ShippingDetail
        fields = ['full_name', 'phone', 'email', 'address', 'pincode', 'city', 'state', 'country']
