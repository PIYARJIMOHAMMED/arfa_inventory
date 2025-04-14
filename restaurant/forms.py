from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'phone_number', 'password1', 'password2']

class LoginForm(forms.Form):
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)



# vendor
from django import forms
from .models import Vendor

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'name', 'phone',
            'gst_no', 'fssai_license_no', 'payment_schedule','is_active'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'payment_schedule': forms.Select(attrs={'class': 'form-control'}),
        }


# raw material

from django import forms
from .models import RawMaterial, Vendor

class RawMaterialForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = [
            'name', 'category', 'unit', 'purchase_price', 
            'minimum_stock_level', 'vendors', 'is_available', 'storage'
        ]

        widgets = {
            'vendors': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


# for purchase 

from django import forms
from .models import Purchase, PurchaseItem, Vendor, RawMaterial
from django import forms
from .models import Purchase

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['vendor', 'invoice_date', 'invoice_no', 'bill_file', 'status', 'payment_mode', 'check_no', 'receiver_name']

        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        payment_mode = cleaned_data.get('payment_mode')
        check_no = cleaned_data.get('check_no')

        if status == 'unpaid':
            return cleaned_data  

        if status == 'paid' and not payment_mode:
            raise forms.ValidationError("Payment mode is required for paid status.")

        if payment_mode == 'check' and not check_no:
            raise forms.ValidationError("Check number is required for check payment.")

        if payment_mode == 'cash':
            if check_no:
                raise forms.ValidationError("Check number should not be provided for cash payments.")

        return cleaned_data


class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['raw_material', 'qty', 'unit', 'price', 'amount', 'tax']

    def __init__(self, *args, **kwargs):
        vendor_id = kwargs.pop('vendor_id', None)
        super().__init__(*args, **kwargs)
        if vendor_id:
            self.fields['raw_material'].queryset = RawMaterial.get_items_by_vendor(vendor_id)

from django import forms
from .models import Purchase

class PurchaseFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    status = forms.ChoiceField(choices=[('', 'All')] + Purchase.STATUS_CHOICES, required=False)




# update stock
from django import forms
from .models import RawMaterial

class ManualStockUpdateForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = ['current_stock']
        widgets = {
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


from django import forms
from .models import ChickenOrder

class ChickenOrderForm(forms.ModelForm):
    class Meta:
        model = ChickenOrder
        fields = ['vendor', 'invoice_date', 'bill_file', 'status', 'payment_mode', 'check_no', 'receiver_name', 'storage_location']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ChickenRateForm(forms.Form):
    big_paper_rate = forms.FloatField(initial=130)
    small_paper_rate = forms.FloatField(initial=150)
    boiler_multiplier = forms.FloatField(initial=1.5)
    mini_multiplier = forms.FloatField(initial=1.5)
    boneless_multiplier = forms.FloatField(initial=2.0)
    wings_multiplier = forms.FloatField(initial=1.5)
    tungdi_multiplier = forms.FloatField(initial=1.5)
    chaap_multiplier = forms.FloatField(initial=1.6)


from django import forms
from .models import Vendor, RawMaterial

class OrderForm(forms.Form):
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.filter(is_active=True), label="Select Vendor")
    items = forms.ModelMultipleChoiceField(queryset=RawMaterial.objects.none(), label="Select Items")
    quantity = forms.IntegerField(min_value=1, label="Quantity")
    ordered_by = forms.CharField(max_length=255, label="Ordered By")

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        if 'vendor' in self.data:
            try:
                vendor_id = int(self.data.get('vendor'))
                self.fields['items'].queryset = RawMaterial.objects.filter(vendors__id=vendor_id)
            except (ValueError, TypeError):
                pass
