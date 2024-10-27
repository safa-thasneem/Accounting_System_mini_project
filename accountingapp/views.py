import csv
import logging
from datetime import datetime
from decimal import Decimal
from lib2to3.fixes.fix_input import context
from re import search

from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.template.loader import get_template

from .forms import ItemForm, CategoryForm, PartyForm, CustomUserCreationForm, PurchaseForm, BillForm
from .models import Item, Category, Parties,  Purchase, PurchaseItem, BillItem, Bill
from xhtml2pdf import pisa

import pdfkit  # You can also use xhtml2pdf, WeasyPrint, etc.



# Home view
def home(request):
    return render(request, 'home.html')  # Home template

def dashboard(request):

    return render(request, 'base.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()  # This ensures the form is always defined

    return render(request, 'register.html', {'form': form})
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard or home page
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('/')

def dashboard_view(request):
    # Your dynamic data can come from your database or calculations
    sales_data = [12000, 15000, 8000, 19000, 13000, 17000]
    months = ['January', 'February', 'March', 'April', 'May', 'June']

    return render(request, 'dashboard.html', {
        'sales_data': sales_data,
        'months': months,
    })



def item_list(request):
    search_query = request.GET.get('search', '')  # Get the search query from the request
    if search_query:
        items = Item.objects.filter(name__icontains=search_query)  # Filter items based on the search query
    else:
        items = Item.objects.all()  # If no search, display all items

    return render(request, 'item_list.html', {'items': items})

# View to add item
# def add_item(request):
#         if request.method == "POST":
#             form = ItemForm(request.POST)
#             if form.is_valid():
#                 item = form.save(commit=False)
#                 item.user = request.user  # Assign the logged-in user
#                 item.save()
#                 return redirect('item_list')  # Redirect to your item list view after saving
#         else:
#             form = ItemForm()
#
#         return render(request, 'add_item.html', {'form': form})
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)

            # Logic for calculating tax and discount
            # if item.has_tax:
            #     item.price += item.price * (item.if_howmuch_tax / Decimal('100.0'))
            #
            # if item.has_discount:
            #     item.price -= item.price * (item.if_howmuch_discount / Decimal('100.0'))

            # item.id should never be assigned manually
            # Save the item with calculated values
            item.save()
            return redirect('item_list')
    else:
        form = ItemForm()

    return render(request, 'add_item.html', {'form': form})

# View to update item
def update_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('item_list')
    else:
        form = ItemForm(instance=item)
    return render(request, 'update_item.html', {'form': form})


# View to delete item
def delete_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('item_list')
    return render(request, 'delete_item.html', {'item': item})


def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()  # Save the category to the database
            return redirect('category_list')  # Redirect to the category list page after saving
    else:
        form = CategoryForm()
    return render(request, 'add_category.html', {'form': form})
def update_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'update_category.html', {'form': form})

def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')

    return render(request, 'delete_category.html', {'category': category})


def category_list(request):
    categories = Category.objects.all()  # Retrieve all categories from the database
    return render(request, 'category_list.html', {'categories': categories})



def party_list(request):
    # parties = Parties.objects.all()
    # Assuming your model is named Parties

        search_query = request.GET.get('search', '')  # Get search query from the request
        if search_query:
            # Filter parties by name or phone number matching the search query
            parties = Parties.objects.filter(name__icontains=search_query) | Parties.objects.filter(
                phone_number__icontains=search_query)
        else:
            parties = Parties.objects.all()  # If no search, display all parties


        return render(request, 'party_list.html', {'parties': parties})

def add_party(request):
    if request.method == 'POST':
        form = PartyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('party_list')
    else:
        form = PartyForm()
    return render(request, 'add_party.html', {'form': form})

# Update a party
def update_party(request, pk):
    party = get_object_or_404(Parties, pk=pk)
    if request.method == 'POST':
        form = PartyForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            return redirect('party_list')
    else:
        form = PartyForm(instance=party)
    return render(request, 'update_party.html', {'form': form})

# Delete a party
def delete_party(request, pk):
    party = get_object_or_404(Parties, pk=pk)
    if request.method == 'POST':
        party.delete()
        return redirect('party_list')
    return render(request, 'delete_party.html', {'party': party})

logger = logging.getLogger(__name__)

def create_bill(request):
    if request.method == "POST":
        # Ensure a party is selected
        party_id = request.POST.get('party')
        if not party_id:
            parties = Parties.objects.all()  # Fetch all parties for dropdown
            items = Item.objects.all()  # Fetch all items for dropdown
            return render(request, 'create_bill.html', {'error': 'Please select a party.', 'parties': parties, 'items': items})

        party = get_object_or_404(Parties, id=party_id)

        # Create a new Bill entry with total_amount initialized to 0
        bill = Bill.objects.create(party=party, total_amount=0)

        # Fetch the selected items and their quantities from the form
        items = request.POST.getlist('item')  # List of item IDs
        quantities = request.POST.getlist('quantities')  # List of corresponding quantities

        if not items or not quantities or len(items) != len(quantities):
            parties = Parties.objects.all()
            items = Item.objects.all()
            return render(request, 'create_bill.html', {'error': 'Please select items and quantities.', 'parties': parties, 'items': items})

        total_amount = 0  # Initialize total amount

        # Loop through selected items and quantities to create BillItem entries
        for item_id, quantity in zip(items, quantities):
            item = get_object_or_404(Item, id=item_id)  # Fetch the item
            quantity = int(quantity)

            # Calculate price with discount and tax
            price_with_discount = item.price - (item.price * item.discount_rate / 100)
            price_with_tax = price_with_discount + (price_with_discount * item.tax_rate / 100)
            subtotal = price_with_tax * quantity
            total_amount += subtotal  # Add to the total amount

            # Log the item details for debugging

            # Create a BillItem entry for each selected item
            BillItem.objects.create(bill=bill, item=item, quantity=quantity, price=subtotal)

        # Update the Bill with the calculated total amount
        bill.total_amount = total_amount
        bill.save()

        logger.info(f"Bill created with total amount: {bill.total_amount}")

        # Redirect to view the generated bill
        return redirect('view_bill', id=bill.id)

    # If GET request, fetch all parties and items to populate the form
    parties = Parties.objects.all()
    items = Item.objects.all()
    return render(request, 'create_bill.html', {'parties': parties, 'items': items})


def view_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    return render(request, 'bill_pdf_template.html', {'bill': bill})




# def create_bill(request):
#     if request.method == 'POST':
#         party_id = request.POST.get('parties')  # Get the selected party
#         items = request.POST.getlist('item')  # Get the selected items
#         quantities = request.POST.getlist('quantities')  # Get the quantities
#
#         # Check if the party ID is valid
#         if not party_id:
#             return render(request, 'create_bill.html', {'error': 'Party must be selected!'})
#
#         # Retrieve the party object and check if it's valid
#         try:
#             party = Parties.objects.get(id=party_id)
#         except Parties.DoesNotExist:
#             return render(request, 'create_bill.html', {'error': 'Selected party not found!'})
#
#         # Calculate totals
#         total_amount = 0.0
#         total_tax = 0.0
#         total_discount = 0.0
#
#         # Validate items
#         if not items or not quantities:
#             return render(request, 'create_bill.html', {'error': 'Items and quantities must be selected!'})
#
#         # Loop through the items and validate them
#         for idx, item_id in enumerate(items):
#             if not item_id:  # If item ID is empty, skip
#                 continue
#
#             try:
#                 item = Item.objects.get(id=item_id)
#             except Item.DoesNotExist:
#                 return render(request, 'create_bill.html', {'error': f'Item with ID {item_id} not found!'})
#
#             quantity = quantities[idx] if quantities else 1
#             if not quantity.isdigit() or int(quantity) < 1:
#                 return render(request, 'create_bill.html', {'error': 'Invalid quantity for item!'})
#
#             quantity = int(quantity)
#             tax_rate = item.tax_rate
#             discount_rate = item.discount_rate
#
#             # Apply discount and tax to the item
#             discounted_price = item.price * (1 - discount_rate / 100)
#             price_with_tax = discounted_price * (1 + tax_rate / 100)
#
#             # Update total amounts
#             subtotal = price_with_tax * quantity
#             total_amount += subtotal
#             total_tax += (discounted_price * quantity * tax_rate / 100)
#             total_discount += (item.price * discount_rate / 100 * quantity)
#
#         # Create the bill
#         bill = Bill.objects.create(
#             party=party,
#             total_amount=total_amount,
#             total_tax=total_tax,
#             total_discount=total_discount
#         )
#
#         # Add items to the bill
#         for idx, item_id in enumerate(items):
#             if not item_id:  # Skip if no item ID
#                 continue
#
#             item = Item.objects.get(id=item_id)
#             quantity = int(quantities[idx])
#
#             BillItem.objects.create(
#                 bill=bill,
#                 item=item,
#                 quantity=quantity
#             )
#
#         return redirect('bill_success')  # Redirect to a success page or bill view
#     else:
#         # Fetch parties and items for the form
#         parties = Parties.objects.all()
#         items = Item.objects.all()
#
#         return render(request, 'create_bill.html', {'parties': parties, 'items': items})


#  Generate and download PDF
def download_bill_pdf(request, bill_id):
    bill = Bill.objects.get(id=bill_id)
    bill_items = BillItem.objects.filter(bill=bill)

    template_path = 'bill_pdf_template.html'
    context = {'bill': bill, 'bill_items': bill_items}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="bill.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    # Generate PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error creating PDF', status=400)

    return response
def purchase_list(request):
    purchases = Purchase.objects.all()
    return render(request, 'purchase_list.html', {'purchases': purchases})

def add_purchase(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('purchase_list')  # Redirect to a purchase list or another view after saving
    else:
        form = PurchaseForm()

    return render(request, 'add_purchase.html', {'form': form})

def update_purchase(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            return redirect('purchase_list')
    else:
        form = PurchaseForm(instance=purchase)

    return render(request, 'update_purchase.html', {'form': form, 'purchase': purchase})

def delete_purchase(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        purchase.delete()
        return redirect('purchase_list')

    return render(request, 'delete_purchase.html', {'purchase': purchase})

def purchase_report(request):
    # Query sales data and aggregate by date or other dimensions
    purchase = Bill.objects.all()

    # Sum of total amount, tax, and discounts
    total_purchase = purchase.aggregate(
        total_amount=Sum('total_amount'),
        total_tax=Sum('total_tax'),
        total_discount=Sum('total_discount')
    )

    context = {
        'purchase': purchase,
        'total_purchase': total_purchase,
    }

    return render(request, 'purchase_report.html', context)




def sales_report(request):
    # Query sales data and aggregate by date or other dimensions
    sales = Bill.objects.all()

    # Sum of total amount, tax, and discounts
    total_sales = sales.aggregate(
        total_amount=Sum('total_amount'),
        total_tax=Sum('total_tax'),
        total_discount=Sum('total_discount')
    )

    context = {
        'sales': sales,
        'total_sales': total_sales,
    }

    return render(request, 'sales_report.html', context)




def download_sales_report(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Party', 'Total Amount', 'Total Tax', 'Total Discount', 'Date'])

    sales = Bill.objects.all()

    for sale in sales:
        writer.writerow([sale.party.name, sale.total_amount, sale.total_tax, sale.total_discount, sale.created_at])
#
#     return response
def report(request):
    return render(request, 'reports.html')


def sales_report_view(request):
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        total_sales = Bill.objects.filter(created_at__range=[start_date, end_date]).aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
    else:
        total_sales = Bill.objects.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0

    context = {
        'total_sales': total_sales,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'sales_report.html', context)

def purchase_report_view(request):
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        total_purchases = Purchase.objects.filter(created_at__range=[start_date, end_date]).aggregate(total_purchases=Sum('total_amount'))['total_purchases'] or 0
    else:
        total_purchases = Purchase.objects.aggregate(total_purchases=Sum('total_amount'))['total_purchases'] or 0

    context = {
        'total_purchases': total_purchases,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'purchase_report.html', context)


def search_party(request):
    query = request.GET.get('q', '')
    if query:
        parties = Parties.objects.filter(name__icontains=query)
    else:
        parties = Parties.objects.none()

    results = [{'id': party.id, 'name': party.name} for party in parties]
    return JsonResponse({'results': results})


# Item search view
def search_item(request):
    query = request.GET.get('q', '')
    if query:
        items = Item.objects.filter(name__icontains=query)
    else:
        items = Item.objects.none()

    results = [{'id': item.id, 'name': item.name, 'price': item.price} for item in items]
    return JsonResponse({'results': results})