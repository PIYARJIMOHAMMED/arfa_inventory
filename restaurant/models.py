from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, unique=True)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username', 'email', 'role']



# vendor

from django.db import models

class Vendor(models.Model):
    PAYMENT_SCHEDULE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('fortnight', 'Fortnight'),
        ('monthly', 'Monthly'),
    ]

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    fssai_license_no = models.CharField(max_length=50, blank=True, null=True)
    items = models.ManyToManyField('RawMaterial', related_name='vendor_items')

    payment_schedule = models.CharField(
        max_length=10,
        choices=PAYMENT_SCHEDULE_CHOICES,
        default='monthly'
    )
    is_active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



# for raw material 

from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

class RawMaterial(models.Model):
    CATEGORY_CHOICES = [
        ('Vegetable', 'Vegetable'),
        ('Grocery', 'Grocery'),
        ('Chicken', 'Chicken'),
        ('Meat', 'Meat'),
        ('Ice', 'Ice'),
        ('Fruit', 'Fruit'),
        ('Oil', 'Oil'),
        ('Packaging Material', 'Packaging Material'),
        ('Soft Drink', 'Soft Drink'),
        ('Coal', 'Coal'),
        ('Dairy Product', 'Dairy Product'),
        ('Cleaning Material', 'Cleaning Material'),
        ('Ice Cream', 'Ice Cream'),
        ('Stationary', 'Stationary'),
        ('Repair and Maintenance', 'Repair and Maintenance'),
        ('Gas', 'Gas'),
        ('Staff Expense', 'Staff Expense')
    ]

    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('gram', 'Gram'),
        ('ltr', 'Liter'),
        ('box', 'Box'),
        ('10kg bag', '10kg Bag'),
        ('25kg bag', '25kg Bag'),
        ('50kg bag', '50kg Bag'),
        ('ml', 'Milliliter'),
        ('bottle', 'Bottle'),
        ('pkts', 'Packets'),
        ('can', 'Can'),
        ('bun', 'Bun'),
        ('extra', 'Extra')
    ]

    STORAGE_CHOICES = [
        ('Supply Room', 'Supply Room'),
        ('Cold Storage', 'Cold Storage')
    ]

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, null=True)
    purchase_price = models.FloatField()
    minimum_stock_level = models.FloatField()
    current_stock = models.FloatField(default=0.0)
    vendors = models.ManyToManyField('Vendor', related_name='raw_material_vendors')
    is_available = models.BooleanField(default=True)
    storage = models.CharField(max_length=50, choices=STORAGE_CHOICES, default='Supply Room')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)  # ✅ Corrected
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_value(self):
        return self.purchase_price * self.current_stock

    def check_threshold(self):
        if self.current_stock <= self.minimum_stock_level:
            self.send_stock_alert()

    def send_stock_alert(self):
        subject = f"Stock Alert: {self.name}"
        message = f"The stock for {self.name} has fallen below the minimum stock level.\n" \
                  f"Current Stock: {self.current_stock}\nMinimum Stock: {self.minimum_stock_level}."
        recipients = [settings.ADMIN_EMAIL]

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)


    @staticmethod
    def get_items_by_vendor(vendor_id):
        return RawMaterial.objects.filter(vendors__id=vendor_id)



# purchase


from django.db import models
from django.contrib.auth.models import User
from .models import Vendor, RawMaterial
import datetime

class Purchase(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('check', 'Check'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    purchase_order_no = models.CharField(max_length=100, unique=True)
    invoice_date = models.DateField()
    invoice_no = models.CharField(max_length=100, unique=True)
    bill_file = models.FileField(upload_to='uploads/vendor_bills/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, null=True, blank=True)
    check_no = models.CharField(max_length=50, null=True, blank=True)  
    receiver_name = models.CharField(max_length=255)
    total_amount = models.FloatField(default=0.0)

    def __str__(self):
        return f"Purchase {self.purchase_order_no} - {self.vendor.name}"

    @staticmethod
    def filter_purchases(start_date=None, end_date=None, status=None):
        queryset = Purchase.objects.all()
        if start_date:
            queryset = queryset.filter(invoice_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(invoice_date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, related_name='items', on_delete=models.CASCADE)
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    qty = models.FloatField()
    unit = models.CharField(max_length=50, choices=[
        ('kg', 'Kilogram'), 
        ('gram', 'Gram'), 
        ('ltr', 'Liter'), 
        ('box', 'Box'),
        ('5kg bag', '5kg Bag'), 
        ('10kg bag', '10kg Bag'), 
        ('25kg bag', '25kg Bag'), 
        ('50kg bag', '50kg Bag'),
        ('ml', 'Milliliter'), 
        ('bottle', 'Bottle'), 
        ('pkts', 'Packets'), 
        ('can', 'Can'), 
        ('bun', 'Bun'), 
        ('extra', 'Extra')
    ])
    price = models.FloatField()
    amount = models.FloatField()
    tax = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.raw_material.name} - {self.purchase.purchase_order_no}"
    def save(self, *args, **kwargs):
        if self.pk:
            self.__original_qty = PurchaseItem.objects.get(pk=self.pk).qty
        else:
            self.__original_qty = 0
        super().save(*args, **kwargs)
    



from django.db import models
from .models import Vendor
from django.utils.crypto import get_random_string

def generate_unique_invoice_no():
    while True:
        new_invoice_no = f"INV{get_random_string(6).upper()}"
        if not ChickenOrder.objects.filter(invoice_no=new_invoice_no).exists():
            return new_invoice_no
        
class ChickenOrder(models.Model):
    STORAGE_CHOICES = [
        ('stock_room', 'Stock Room'),
        ('cold_storage', 'Cold Storage'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    invoice_date = models.DateField()
    invoice_no = models.CharField(max_length=50, unique=True, default=generate_unique_invoice_no)
    bill_file = models.FileField(upload_to='uploads/chicken_orders/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')], default='unpaid')
    payment_mode = models.CharField(max_length=10, choices=[('cash', 'Cash'), ('upi', 'UPI'), ('card', 'Card'), ('check', 'Check')], null=True, blank=True)
    check_no = models.CharField(max_length=50, null=True, blank=True)
    receiver_name = models.CharField(max_length=255)
    storage_location = models.CharField(max_length=20, choices=STORAGE_CHOICES, default='stock_room')
    total_amount = models.FloatField(default=0.0)
 
    def __str__(self):
        return f"Chicken Order {self.invoice_no} - {self.vendor.name}"
