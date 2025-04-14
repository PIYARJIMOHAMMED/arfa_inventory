from django.urls import path
from .views import register_view, login_view
from .views import dashboard
from .views import add_vendor, vendor_list, edit_vendor, delete_vendor, export_vendors
from .views import raw_material_list, add_raw_material, edit_raw_material
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard, name='inventory_dashboard'),
    path('vendor/add/', add_vendor, name='add_vendor'),
    path('vendor/', vendor_list, name='vendor_list'),
    path('vendor/edit/<int:vendor_id>/', edit_vendor, name='edit_vendor'),
    path('vendor/delete/<int:vendor_id>/', delete_vendor, name='delete_vendor'),
    path('vendor/export/', export_vendors, name='export_vendors'),
    path('add-raw-material/', views.add_raw_material, name='add_raw_material'),
    path('raw-materials/', views.raw_material_list, name='raw_material_list'),
    path('raw-material/add/', views.add_raw_material, name='add_raw_material'),
    path('vendor/<int:vendor_id>/items/', views.vendor_items, name='vendor_items'),
    path('raw-material/edit/<int:pk>/', edit_raw_material, name='edit_raw_material'),
    path('add-purchase/', views.add_purchase, name='add_purchase'),
    path('add-purchase-item/<int:purchase_id>/', views.add_purchase_item, name='add_purchase_item'),
    path('daily_purchase_summary/', views.daily_purchase_summary, name='daily_purchase_summary'),
    path('generate-pdf/<int:purchase_id>/', views.generate_pdf, name='generate_pdf'),
    path('purchase-history/', views.purchase_history, name='purchase_history'),
    path('payment/', views.payment, name='payment'),
    path('export-purchases/', views.export_purchases, name='export_purchases'),  
    path('add-chicken-order/', views.add_chicken_order, name='add_chicken_order'),
    path('chicken-rate-entry/', views.chicken_rate_entry, name='chicken_rate_entry'),
    path('save-chicken-order/', views.save_chicken_order, name='save_chicken_order'),
    path('stock-book/', views.stock_book, name='stock_book'),
    path('stock-room/', views.stock_room_view, name='stock_room'),
    path('cold-storage/', views.cold_storage_view, name='cold_storage'),

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


