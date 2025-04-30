from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.utils.timezone import now
from datetime import timedelta
from .models import CustomUser
from .forms import RegistrationForm, LoginForm


from django.http import HttpResponse

#def home(request):
 #   return HttpResponse("Welcome to Cafe Inventory!")


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            user = CustomUser.objects.filter(phone_number=phone_number).first()

            if user:
                if user.last_login and (now() - user.last_login) <= timedelta(days=7):
                    login(request, user)
                    return redirect('inventory_dashboard')  # ✅ Fix applied here
                elif user.last_login and (now() - user.last_login) > timedelta(days=15):
                    return redirect('otp_verification')  
                else:
                    user = authenticate(request, phone_number=phone_number, password=password)
                    if user:
                        login(request, user)
                        return redirect('inventory_dashboard')  # ✅ Fix applied here
                    else:
                        return render(request, 'login.html', {'form': form, 'error': 'Invalid credentials'})
            else:
                return render(request, 'login.html', {'form': form, 'error': 'User does not exist'})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')



# vendor

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
import openpyxl
from .models import Vendor
from .forms import VendorForm

def add_vendor(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor added successfully!')
            return redirect('vendor_list') 
    else:
        form = VendorForm()
    return render(request, 'inventory/add_vendor.html', {'form': form})

def vendor_list(request):
    vendors = Vendor.objects.all()
    query = request.GET.get('q')
    if query:
        vendors = vendors.filter(name__icontains=query)
    return render(request, 'inventory/vendor_list.html', {'vendors': vendors})

def edit_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor updated successfully!')
            return redirect('vendor_list')
    else:
        form = VendorForm(instance=vendor)
    return render(request, 'inventory/edit_vendor.html', {'form': form, 'vendor': vendor})

def delete_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.delete()
    messages.success(request, 'Vendor deleted successfully!')
    return redirect('vendor_list')

def export_vendors(request):
    vendors = Vendor.objects.all()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Vendors"

    headers = ['Name', 'Company', 'Phone', 'GST No', 'FSSAI License No', 'Status']
    sheet.append(headers)

    for vendor in vendors:
        sheet.append([
            vendor.name, vendor.company, vendor.phone,
            vendor.gst_no, vendor.fssai_license_no, 'Active' if vendor.status else 'Inactive'
        ])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename="vendors.xlsx"'
    workbook.save(response)
    return response


# for raw material

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import RawMaterial, Vendor
from .forms import RawMaterialForm


def add_raw_material(request):
    if request.method == 'POST':
        form = RawMaterialForm(request.POST)
        if form.is_valid():
            raw_material = form.save(commit=False)
            raw_material.save()
            form.save_m2m()
            return redirect('raw_material_list')
    else:
        form = RawMaterialForm()
    return render(request, 'inventory/add_raw_material.html', {'form': form})

def raw_material_list(request):
    raw_materials = RawMaterial.objects.all()
    return render(request, 'inventory/raw_material_list.html', {'materials': raw_materials})

def vendor_items(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    items = RawMaterial.get_items_by_vendor(vendor_id)
    return render(request, 'inventory/vendor_items.html', {'vendor': vendor, 'items': items})

def edit_raw_material(request, pk):
    raw_material = get_object_or_404(RawMaterial, pk=pk)
    if request.method == 'POST':
        form = RawMaterialForm(request.POST, instance=raw_material)
        if form.is_valid():
            form.save()
            return redirect('raw_material_list')
    else:
        form = RawMaterialForm(instance=raw_material)
    return render(request, 'inventory/add_raw_material.html', {'form': form})



# purchase


# for purchae
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Purchase, PurchaseItem, Vendor, RawMaterial
from .forms import PurchaseForm, PurchaseItemForm
import datetime
from django.db import models  


def generate_purchase_order_no():
    return f"PO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

def add_purchase(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST, request.FILES)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.purchase_order_no = generate_purchase_order_no()
            purchase.total_amount = 0.0
            purchase.save()
            return redirect('add_purchase_item', purchase_id=purchase.id)
    else:
        form = PurchaseForm()

    return render(request, 'inventory/add_purchase.html', {'form': form})

def add_purchase_item(request, purchase_id):
    purchase = Purchase.objects.get(id=purchase_id)
    form = PurchaseItemForm(request.POST or None, vendor_id=purchase.vendor.id)

    if request.method == 'POST':
        if form.is_valid():
            item = form.save(commit=False)
            item.purchase = purchase
            item.amount = item.qty * item.price + item.tax
            item.save()
            purchase.total_amount += item.amount
            purchase.save()
            form = PurchaseItemForm(vendor_id=purchase.vendor.id)

    items = purchase.items.all()
    return render(request, 'inventory/add_purchase_item.html', {
        'form': form,
        'purchase': purchase,
        'items': items,
    })




from django.shortcuts import render
from .models import Purchase
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO


def payment(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    payment_mode = request.GET.get('payment_mode')

    purchases = Purchase.objects.all()
    if start_date:
        purchases = purchases.filter(invoice_date__gte=start_date)
    if end_date:
        purchases = purchases.filter(invoice_date__lte=end_date)
    if payment_mode:
        purchases = purchases.filter(payment_mode=payment_mode)

    return render(request, 'inventory/payment.html', {'purchases': purchases})


def generate_pdf(request, purchase_id):
    purchase = Purchase.objects.get(id=purchase_id)
    items = purchase.items.all()
    template = get_template('inventory/purchase_pdf.html')
    html = template.render({'purchase': purchase, 'items': items})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="purchase_{purchase_id}.pdf"'

    pisa_status = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=400)
    return response


from django.shortcuts import render
from .models import Purchase, ChickenOrder
from .forms import PurchaseFilterForm
import csv


def purchase_history(request):
    purchases = Purchase.objects.all()
    chicken_orders = ChickenOrder.objects.all()
    
    form = PurchaseFilterForm(request.GET)
    
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        status = form.cleaned_data.get('status')
        
        if start_date and end_date:
            purchases = purchases.filter(invoice_date__range=[start_date, end_date])
        
        if status:
            purchases = purchases.filter(status=status)


    return render(request, 'inventory/purchase_history.html', {
        'purchases': purchases,
        'form': form
    })


def export_purchases(request):
    purchases = Purchase.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="purchases.csv"'

    writer = csv.writer(response)
    writer.writerow(['Invoice No', 'Vendor', 'Invoice Date', 'Status', 'Total Amount', 'Receiver Name'])
    for purchase in purchases:
        writer.writerow([
            purchase.invoice_no,
            purchase.vendor.name,
            purchase.invoice_date,
            purchase.status,
            purchase.total_amount,
            purchase.receiver_name,
        ])

    return response



def generate_purchase_order_no():
    return f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"


from django.shortcuts import render, redirect
from .forms import ChickenOrderForm, ChickenRateForm
from .models import ChickenOrder

def add_chicken_order(request):
    if request.method == 'POST':
        form = ChickenOrderForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('chicken_rate_entry')
    else:
        form = ChickenOrderForm()

    return render(request, 'inventory/add_chicken_order.html', {'form': form})

def chicken_rate_entry(request):
    if request.method == 'POST':
        form = ChickenRateForm(request.POST)
        if form.is_valid():
            big_rate = form.cleaned_data['big_paper_rate']
            small_rate = form.cleaned_data['small_paper_rate']
            calculations = {
                'boiler': big_rate * form.cleaned_data['boiler_multiplier'],
                'mini': small_rate * form.cleaned_data['mini_multiplier'],
                'boneless': big_rate * form.cleaned_data['boneless_multiplier'],
                'wings': big_rate * form.cleaned_data['wings_multiplier'],
                'tungdi': big_rate * form.cleaned_data['tungdi_multiplier'],
                'chaap': small_rate * form.cleaned_data['chaap_multiplier'],
            }
            return render(request, 'inventory/chicken_rate_calculation.html', {'form': form, 'calculations': calculations})
    else:
        form = ChickenRateForm()

    return render(request, 'inventory/chicken_rate_entry.html', {'form': form})


from django.http import HttpResponse
from datetime import datetime
from django.template.loader import render_to_string
import pdfkit  # OR weasyprint if you prefer
from django.shortcuts import render, redirect, get_object_or_404
from .models import ChickenOrder, Vendor, Purchase, generate_unique_invoice_no
from .models import RawMaterial

def save_chicken_order(request):
    if request.method == 'POST':
        try:
            print_choice = request.POST.get('print_choice', 'no')
            invoice_date = request.POST.get('invoice_date') or datetime.today().date()
            receiver_name = request.POST.get('receiver_name', 'Auto Receiver')
            items = ['boiler', 'mini', 'boneless', 'wings', 'tungdi', 'chaap']
            total_amount = 0
            order_items = []

            for item in items:
                rate = float(request.POST.get(f'rate_{item}', 0))
                qty = float(request.POST.get(f'qty_{item}', 0))
                amount = rate * qty
                if qty > 0:
                    order_items.append({'item': item, 'rate': rate, 'qty': qty, 'amount': amount})
                    total_amount += amount

                    # Update stock or create new item
                    raw_item, created = RawMaterial.objects.get_or_create(
                        name=item,
                        category='Meat & Poultry',
                        defaults={
                            'unit': 'kg',
                            'purchase_price': rate,
                            'current_stock': 0,
                            'storage': 'Meat & Poultry',
                            'minimum_stock_level': 0  # ✅ Add this line
                        }
                    )

                    raw_item.current_stock += qty
                    raw_item.purchase_price = rate
                    raw_item.save()

            invoice_no = generate_unique_invoice_no()
            vendor = get_object_or_404(Vendor, name__iexact="Shah supplier")

            ChickenOrder.objects.create(
                vendor=vendor,
                invoice_no=invoice_no,
                invoice_date=invoice_date,
                total_amount=total_amount,
                receiver_name=receiver_name,
            )

            if print_choice == 'yes':
                html = render_to_string("inventory/print_bill.html", {
                    'invoice_no': invoice_no,
                    'invoice_date': invoice_date,
                    'items': order_items,
                    'total': total_amount
                })
                return HttpResponse(html)

            return HttpResponse(f"Order saved successfully! Invoice No: {invoice_no}, Total: {total_amount}")
        except Exception as e:
            return HttpResponse(f"Error: {e}", status=400)

    return redirect('chicken_rate_entry')


# daily purchase summary

from django.db import models
from django.shortcuts import render
from itertools import chain
from .models import Purchase, ChickenOrder

def daily_purchase_summary(request):
    # Query regular purchases
    regular_purchases = Purchase.objects.values('invoice_date').annotate(
        total_amount=models.Sum('total_amount'),
        total_purchases=models.Count('id'),
    )

    # Query chicken purchases
    chicken_purchases = ChickenOrder.objects.values('invoice_date').annotate(
        total_amount=models.Sum('total_amount'),
        total_purchases=models.Count('id'),
    )

    # Combine both querysets into one list
    combined_purchases = list(chain(regular_purchases, chicken_purchases))

    # Group the purchases by date to merge values with the same date
    summary = {}
    for purchase in combined_purchases:
        date = purchase['invoice_date']
        if date in summary:
            summary[date]['total_amount'] += purchase['total_amount'] or 0
            summary[date]['total_purchases'] += purchase['total_purchases']
        else:
            summary[date] = {
                'invoice_date': date,
                'total_amount': purchase['total_amount'] or 0,
                'total_purchases': purchase['total_purchases'],
            }

    # Convert summary dictionary back to list for template rendering
    summarized_purchases = sorted(summary.values(), key=lambda x: x['invoice_date'])

    return render(request, 'inventory/daily_purchase_summary.html', {
        'purchases': summarized_purchases
    })



# stock book

from django.shortcuts import render
from django.db.models import Sum
from .models import RawMaterial

def stock_book(request):
    total_items = RawMaterial.objects.count()
    stock_room_items = RawMaterial.objects.filter(storage='Supply Room').count()
    cold_storage_items = RawMaterial.objects.filter(storage='Cold Storage').count()
    meat_poultry_view = RawMaterial.objects.filter(storage='Meat & Poultry').count()

    total_stock_value = RawMaterial.objects.aggregate(
        total_value=Sum('purchase_price')
    )['total_value'] or 0

    return render(request, 'inventory/stock_book.html', {
        'total_items': total_items,
        'stock_room_items': stock_room_items,
        'cold_storage_items': cold_storage_items,
        'meat_poultry_view': meat_poultry_view,
        'total_stock_value': total_stock_value,
    })

def stock_room_view(request):
    stock_room_items = RawMaterial.objects.filter(storage='Supply Room')
    return render(request, 'inventory/stock_room.html', {'items': stock_room_items})

def cold_storage_view(request):
    cold_storage_items = RawMaterial.objects.filter(storage='Cold Storage')
    return render(request, 'inventory/cold_storage.html', {'items': cold_storage_items})


def meat_poultry_view(request):
    poultry_items = RawMaterial.objects.filter(storage='Meat & Poultry')

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        item = get_object_or_404(RawMaterial, id=item_id)
        form = ManualStockUpdateForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            item.check_threshold()
            messages.success(request, f"{item.name} updated successfully!")
        else:
            messages.error(request, "Failed to update stock.")

    total_value = sum(item.total_value() for item in poultry_items)

    return render(request, 'inventory/meat_poultry_room.html', {
        'items': poultry_items,
        'total_value': total_value,
        'form': ManualStockUpdateForm(),
    })

# views.py
from django.utils.timezone import now
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import RawMaterial, DailyReport, DailyStockReport, LowStockAlert

def meat_poultry_close_day_view(request):
    poultry_items = RawMaterial.objects.filter(storage='Meat & Poultry')

    if request.method == 'POST':
        today = now().date()

        daily_report, created = DailyReport.objects.get_or_create(
            date=today,
            defaults={'storage': 'Meat & Poultry'}
        )

        if not created and daily_report.storage != 'Meat & Poultry':
            daily_report.storage = 'Meat & Poultry'
            daily_report.save()

        low_stock_items = []

        for item in poultry_items:
            opening_stock = item.current_stock
            entered_closing_stock = float(request.POST.get(f'closing_stock_{item.id}', opening_stock))
            used_stock = opening_stock - entered_closing_stock

            report_entry, created = DailyStockReport.objects.get_or_create(
                report=daily_report,
                item=item,
                defaults={
                    'opening_stock': opening_stock,
                    'closing_stock': entered_closing_stock,
                    'used_stock': used_stock
                }
            )

            if not created:
                report_entry.opening_stock = opening_stock
                report_entry.closing_stock = entered_closing_stock
                report_entry.used_stock = used_stock
                report_entry.save()

            item.current_stock = entered_closing_stock
            item.save()

            if entered_closing_stock < item.minimum_stock_level:
                LowStockAlert.objects.create(
                    item=item,
                    current_stock=entered_closing_stock,
                    minimum_stock_level=item.minimum_stock_level
                )
                low_stock_items.append(item)

        if low_stock_items:
            send_low_stock_pdf_report(low_stock_items)

        messages.success(request, "Meat & Poultry Day closed and report generated.")
        return redirect('meat_poultry_daily_report_list')

    return render(request, 'inventory/meat_poultry_close_day_form.html', {'items': poultry_items})
from django.views.generic import ListView, DetailView
from datetime import datetime

class MeatPoultryDailyReportListView(ListView):
    model = DailyReport
    template_name = 'inventory/meat_poultry_daily_report_list.html'
    context_object_name = 'reports'

    def get_queryset(self):
        return DailyReport.objects.filter(storage='Meat & Poultry').order_by('-date')
class MeatPoultryDailyReportDetailView(DetailView):
    model = DailyReport
    template_name = 'inventory/meat_poultry_daily_report_detail.html'
    context_object_name = 'report'

    def get_object(self):
        date_str = self.kwargs.get('date')
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return get_object_or_404(DailyReport, date=parsed_date, storage='Meat & Poultry')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = self.object.daily_stock_reports.filter(item__storage='Meat & Poultry')
        return context



from .models import RawMaterial, DailyStockReport, LowStockAlert, DailyReport
from django.core.mail import send_mail
from django.conf import settings
from .forms import ManualStockUpdateForm


def stock_room_view(request):
    stock_room_items = RawMaterial.objects.filter(storage='Supply Room')

    if request.method == 'POST':
        if 'close_day' in request.POST:
            today = now().date()
            daily_report, created = DailyReport.objects.get_or_create(date=today)

            for item in stock_room_items:
                opening_stock = item.current_stock
                used_stock = item.current_stock - float(request.POST.get(f'current_stock_{item.id}', item.current_stock))
                
                stock_report, created = DailyStockReport.objects.get_or_create(
                    report=daily_report,
                    item=item,
                    defaults={
                        'opening_stock': opening_stock + used_stock,
                        'closing_stock': item.current_stock,
                        'used_stock': used_stock,
                    }
                )

                if not created:
                    # Update the existing stock report
                    stock_report.opening_stock = opening_stock + used_stock
                    stock_report.closing_stock = item.current_stock
                    stock_report.used_stock = used_stock
                    stock_report.save()

            messages.success(request, "Day closed and report generated successfully!")
            return redirect('daily_report_list')

        else:
            # Regular stock update
            item_id = request.POST.get('item_id')
            item = get_object_or_404(RawMaterial, id=item_id)
            form = ManualStockUpdateForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                item.check_threshold()
                # After update, check stock threshold
                if item.current_stock < item.minimum_stock_level:
                    LowStockAlert.objects.create(
                        item=item,
                        current_stock=item.current_stock,
                        minimum_stock_level=item.minimum_stock_level
                    )
                    send_low_stock_pdf_report(item)
                messages.success(request, f"{item.name} stock updated successfully!")
            else:
                messages.error(request, "Failed to update stock.")

    total_value = sum(item.total_value() for item in stock_room_items)

    return render(request, 'inventory/stock_room.html', {
        'items': stock_room_items,
        'total_value': total_value,
        'form': ManualStockUpdateForm(),
    })


from django.views.generic import ListView, DetailView
class DailyReportListView(ListView):
    model = DailyReport
    template_name = 'inventory/daily_report_list.html'
    context_object_name = 'reports'
    ordering = ['-date']


from django.shortcuts import get_object_or_404

from django.utils.timezone import now
from datetime import datetime

class daily_report_detail_view(DetailView):
    model = DailyReport
    template_name = 'inventory/daily_report_detail.html'
    context_object_name = 'report'

    def get_object(self):
        date_str = self.kwargs.get('date')  # get date from URL
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return get_object_or_404(DailyReport, date=date)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock_reports'] = self.object.daily_stock_reports.filter(item__storage='Supply Room')
        return context



import io
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Avg

def close_day_view(request):
    stock_room_items = RawMaterial.objects.filter(storage='Supply Room')

    if request.method == 'POST':
        today = now().date()
        daily_report, created = DailyReport.objects.get_or_create(date=today)
        low_stock_items = []

        for item in stock_room_items:
            opening_stock = item.current_stock
            entered_closing_stock = float(request.POST.get(f'closing_stock_{item.id}', opening_stock))
            used_stock = opening_stock - entered_closing_stock

            # Save to DailyStockReport
            stock_report, created = DailyStockReport.objects.get_or_create(
                report=daily_report,
                item=item,
                defaults={
                    'opening_stock': opening_stock,
                    'closing_stock': entered_closing_stock,
                    'used_stock': used_stock,
                }
            )
            if not created:
                stock_report.opening_stock = opening_stock
                stock_report.closing_stock = entered_closing_stock
                stock_report.used_stock = used_stock
                stock_report.save()

            # Update RawMaterial current stock
            item.current_stock = entered_closing_stock
            item.save()

            # Check for low stock
            if entered_closing_stock < item.minimum_stock_level:
                LowStockAlert.objects.create(
                    item=item,
                    current_stock=entered_closing_stock,
                    minimum_stock_level=item.minimum_stock_level
                )
                low_stock_items.append(item)

        # Generate and send low stock report if needed
        if low_stock_items:
            send_low_stock_pdf_report(low_stock_items)

        messages.success(request, "Day closed and report generated successfully!")
        return redirect('daily_report_list')

    return render(request, 'inventory/close_day_form.html', {'items': stock_room_items})

def send_low_stock_pdf_report(low_stock_items):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 50, "Low Stock Report")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, f"Date: {now().date().strftime('%d %b %Y')}")

    y = height - 100
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Item")
    p.drawString(200, y, "Current Stock")
    p.drawString(320, y, "Min Required")
    p.drawString(450, y, "Avg Daily Usage")

    p.setFont("Helvetica", 11)
    y -= 20
    for item in low_stock_items:
        avg_usage = DailyStockReport.objects.filter(item=item).aggregate(avg=Avg('used_stock'))['avg'] or 0.0
        p.drawString(50, y, item.name)
        p.drawString(200, y, f"{item.current_stock}")
        p.drawString(320, y, f"{item.minimum_stock_level}")
        p.drawString(450, y, f"{round(avg_usage, 2)}")
        y -= 20

    p.showPage()
    p.save()
    buffer.seek(0)

    email = EmailMessage(
        subject="🚨 Low Stock Report",
        body="Please find attached today's low stock report.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_EMAIL]
    )
    email.attach('LowStockReport.pdf', buffer.read(), 'application/pdf')
    email.send()



from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from .models import RawMaterial, Vendor


# Fetch vendors for a specific item
def get_vendors_for_item(request, item_id):
    item = get_object_or_404(RawMaterial, id=item_id)
    vendors = Vendor.objects.filter(items__id=item_id).values('id', 'name')
    return JsonResponse({'vendors': list(vendors)})

from django.db.models import Sum, F
from .models import RawMaterial, DailyStockReport, LowStockAlert, DailyReport
from django.utils.timezone import now
from django.core.mail import EmailMessage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg
import io


def cold_storage_view(request):
    cold_storage_items = RawMaterial.objects.filter(storage='Cold Storage')

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        current_stock = request.POST.get('current_stock')

        try:
            item = get_object_or_404(RawMaterial, id=item_id)
            item.current_stock = float(current_stock)
            item.save()
            item.check_threshold()
            messages.success(request, f"{item.name} stock updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating stock: {e}")

    total_value = cold_storage_items.aggregate(
        total=Sum(F('current_stock') * F('purchase_price'))
    )['total'] or 0

    return render(request, 'inventory/cold_storage.html', {
        'items': cold_storage_items,
        'total_value': round(total_value, 2)
    })


def cold_storage_close_day_view(request):
    cold_storage_items = RawMaterial.objects.filter(storage='Cold Storage')

    if request.method == 'POST':
        today = now().date()

        daily_report, created = DailyReport.objects.get_or_create(
            date=today,
            storage='Cold Storage',
            defaults={'storage': 'Cold Storage'}
        )


        if not created and daily_report.storage != 'Cold Storage':
            daily_report.storage = 'Cold Storage'
            daily_report.save()

        low_stock_items = []

        for item in cold_storage_items:
            opening_stock = item.current_stock
            entered_closing_stock = float(request.POST.get(f'closing_stock_{item.id}', opening_stock))
            used_stock = opening_stock - entered_closing_stock

            report_entry, created = DailyStockReport.objects.get_or_create(
                report=daily_report,
                item=item,
                defaults={
                    'opening_stock': opening_stock,
                    'closing_stock': entered_closing_stock,
                    'used_stock': used_stock
                }
            )

            if not created:
                report_entry.opening_stock = opening_stock
                report_entry.closing_stock = entered_closing_stock
                report_entry.used_stock = used_stock
                report_entry.save()

            item.current_stock = entered_closing_stock
            item.save()

            if entered_closing_stock < item.minimum_stock_level:
                LowStockAlert.objects.create(
                    item=item,
                    current_stock=entered_closing_stock,
                    minimum_stock_level=item.minimum_stock_level
                )
                low_stock_items.append(item)

        if low_stock_items:
            send_low_stock_pdf_report(low_stock_items)

        messages.success(request, "Cold Storage day closed and report generated.")
        return redirect('cold_storage_daily_report_list')

    return render(request, 'inventory/cold_storage_close_day_form.html', {'items': cold_storage_items})



class ColdStorageDailyReportListView(ListView):
    model = DailyReport
    template_name = 'inventory/cold_storage_daily_report_list.html'
    context_object_name = 'reports'

    def get_queryset(self):
        return DailyReport.objects.filter(storage='Cold Storage').order_by('-date')


class ColdStorageDailyReportDetailView(DetailView):
    model = DailyReport
    template_name = 'inventory/cold_storage_daily_report_detail.html'
    context_object_name = 'report'

    def get_object(self):
        date_str = self.kwargs.get('date')
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return get_object_or_404(DailyReport, date=parsed_date, storage='Cold Storage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = self.object.daily_stock_reports.filter(item__storage='Cold Storage')
        return context




from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PurchaseItem, RawMaterial

@receiver(post_save, sender=PurchaseItem)
def update_stock_on_purchase_item_save(sender, instance, created, **kwargs):
    """Update RawMaterial stock when a PurchaseItem is created or updated."""
    raw_material = instance.raw_material
    if created:
        raw_material.current_stock += instance.qty
    else:
        raw_material.current_stock += instance.qty - instance.__original_qty
    raw_material.save()

@receiver(post_delete, sender=PurchaseItem)
def update_stock_on_purchase_item_delete(sender, instance, **kwargs):
    """Decrease RawMaterial stock when a PurchaseItem is deleted."""
    raw_material = instance.raw_material
    raw_material.current_stock -= instance.qty
    raw_material.save()


from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from .models import RawMaterial, Vendor
import urllib.parse

def get_vendors_for_item(request, item_id):
    item = get_object_or_404(RawMaterial, id=item_id)
    vendors = Vendor.objects.filter(items__id=item_id).values('id', 'name')
    return JsonResponse({'vendors': list(vendors)})


