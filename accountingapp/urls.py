from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/update/<int:pk>/', views.update_category, name='update_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('categories/', views.category_list, name='category_list'),
    path('items/add/', views.add_item, name='add_item'),
    path('items/update/<int:pk>/', views.update_item, name='update_item'),
    path('items/delete/<int:pk>/', views.delete_item, name='delete_item'),
    path('items/', views.item_list, name='item_list'),
    path('parties/', views.party_list, name='party_list'),
    path('parties/add/', views.add_party, name='add_party'),
    path('parties/update/<int:pk>/', views.update_party, name='update_party'),
    path('parties/delete/<int:pk>/', views.delete_party, name='delete_party'),
    path('billings/add/', views.create_bill, name='create_bill'),
    path('purchase/add/', views.add_purchase, name='add_purchase'),
    path('purchase/update/<int:pk>/', views.update_purchase, name='update_purchase'),
    path('purchase/delete/<int:pk>/', views.delete_purchase, name='delete_purchase'),
    # path('bill/create/', views.create_bill, name='create_bill'),
    path('create_bill/', views.create_bill, name='create_bill'),
    path('view_bill/<int:bill_id>/', views.view_bill, name='view_bill'),

    # Path for viewing a specific bill (e.g., after saving)
    # path('bill/<int:bill_id>/', views.view_bill, name='view_bill'),

    # Path for downloading a bill as a PDF
    path('bill/<int:bill_id>/pdf/', views.download_bill_pdf, name='download_bill_pdf'),

    path('reports/', views.report, name='report'),
    path('reports/sales/', views.sales_report, name='sales_report'),  # Ensure this URL pattern exists
    path('reports/purchase/', views.purchase_report, name='purchase_report'),  # Ensure this URL pattern exists
    path('sales-report/', views.sales_report_view, name='sales_report_view'),
    path('purchase-report/', views.purchase_report_view, name='purchase_report_view'),
    path('search-party/', views.search_party, name='search_party'),
    path('search-item/', views.search_item, name='search_item'),
]