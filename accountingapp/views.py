import csv
from datetime import datetime
import logging
from django.contrib import messages
from django.urls import reverse

from decimal import Decimal
from lib2to3.fixes.fix_input import context
from re import search

from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Q, F
from django.db.models.functions import TruncMonth, ExtractYear
from django.http import HttpResponse, JsonResponse, request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone

from .forms import ItemForm, CategoryForm, PartyForm, CustomUserCreationForm, PurchaseForm, BillForm
from .models import Item, Category, Parties,  Purchase, PurchaseItem, BillItem, Bill
from xhtml2pdf import pisa

import pdfkit  # You can also use xhtml2pdf, WeasyPrint, etc.



# Home view
def home(request):
    return render(request, 'home.html')  # Home template

def dashboard(request):

    return render(request, 'base.html')

def dashboard_view(request):
    # Aggregate data by year instead of day-by-day
    sales = Bill.objects.annotate(year=ExtractYear('created_at')).values('year').annotate(total=Sum('total_amount'))
    purchases = Purchase.objects.annotate(year=ExtractYear('created_at')).values('year').annotate(total=Sum('total_amount'))

    # Process the data
    sales_data = [float(sale['total']) for sale in sales]
    purchase_data = [float(purchase['total']) for purchase in purchases]

    # Extract the year labels
    labels = [sale['year'] for sale in sales]

    # Calculate profit/loss data for each year
    profit_loss_data = [
        sales_data[i] - purchase_data[i] if i < len(purchase_data) else sales_data[i]
        for i in range(len(sales_data))
    ]

    context = {
        'sales_data': sales_data,
        'purchase_data': purchase_data,
        'profit_loss_data': profit_loss_data,
        'labels': labels,
    }
    return render(request, 'dashboard.html', context)

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

# def dashboard_view(request):
#     sales_data = Bill.objects.values('date').annotate(total_sales=Sum('amount'))
#     purchase_data = Purchase.objects.values('date').annotate(total_purchases=Sum('amount'))
#
#     # Convert to list for easier JSON serialization
#     sales_dates = [entry['date'] for entry in sales_data]
#     total_sales = [entry['total_sales'] for entry in sales_data]
#     total_purchases = [entry['total_purchases'] for entry in purchase_data]
#
#     context = {
#         'sales_dates': sales_dates,
#         'total_sales': total_sales,
#         'total_purchases': total_purchases,
#     }
#     return render(request, 'dashboard.html', context)

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
        print("Received form data:", request.POST)

        party_id = request.POST.get('party')
        if not party_id:
            parties = Parties.objects.all()
            items = Item.objects.all()
            return render(request, 'create_bill.html', {
                'error': 'Please select a party.',
                'parties': parties,
                'items': items
            })

        party = get_object_or_404(Parties, id=party_id)
        print("Selected party:", party)

        bill = Bill.objects.create(party=party, total_amount=0, total_tax=0, total_discount=0)

        # Retrieve hidden items and convert to list of integers
        hidden_items = request.POST.get('hidden_items', '')
        item_ids = [int(item_id) for item_id in hidden_items.split(',') if item_id.isdigit()]

        quantities = request.POST.getlist('quantities')

        # Combine item IDs with their respective quantities
        items_and_quantities = [(item_id, quantity) for item_id, quantity in zip(item_ids, quantities) if
                                item_id and quantity]

        print("Filtered items and quantities:", items_and_quantities)

        if not items_and_quantities:
            parties = Parties.objects.all()
            items = Item.objects.all()
            messages.error(request, 'Please select items and quantities.')  # Use messages framework

            return render(request, 'create_bill.html', {
                'error': 'Please select items and quantities.',
                'parties': parties,
                'items': items
            })

        total_amount = 0
        total_tax = 0
        total_discount = 0

        # Process each valid item and its quantity
        for item_id, quantity in items_and_quantities:
            item = get_object_or_404(Item, id=item_id)  # Ensure item_id is an integer
            quantity = int(quantity)

            if item.stock_level < quantity:
                messages.error(request, f'Item "{item.name}" is out of stock, please select another item.')
                # Rollback: delete bill and redirect to the form page
                bill.delete()
                return redirect('check_low_stock')  # Assuming 'create_bill' is the URL name for the bill creation page
            discount_amount = item.price * item.discount_rate / 100
            discounted_price = item.price - discount_amount  # Price after discount
            tax_amount = discounted_price * item.tax_rate / 100

            print(f"Item: {item.name}, Price: {item.price}, Discount: {discount_amount}, Tax: {tax_amount}")

            subtotal = (discounted_price + tax_amount) * quantity
            total_amount += subtotal
            total_tax += tax_amount * quantity
            total_discount += discount_amount * quantity
            BillItem.objects.create(bill=bill, item=item, quantity=quantity)
            # ... your existing sale logic ...
            item.stock_level -= quantity  # Decrease stock level
            item.save()

        print("Total Amount:", total_amount)
        print("Total Tax:", total_tax)
        print("Total Discount:", total_discount)

        # Update the bill totals
        bill.total_amount = total_amount
        bill.total_tax = total_tax
        bill.total_discount = total_discount
        bill.save()

        return redirect(reverse('view_bill', kwargs={'bill_id': bill.id}))

    # GET request handling
    parties = Parties.objects.all()
    items = Item.objects.all()
    return render(request, 'create_bill.html', {'parties': parties, 'items': items})

def view_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    bill_items = BillItem.objects.filter(bill=bill)  # Get all items for the bill

    context = {
        'bill': bill,
        'bill_items': bill_items,
    }
    return render(request, 'bill_pdf_template.html', context)



#  Generate and download PDF
def download_bill_pdf(request,bill_id):
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

# def create_purchase(request):
#     if request.method == "POST":
#         print("Received form data:", request.POST)
#
#         party_id = request.POST.get('party')
#         if not party_id:
#             parties = Parties.objects.all()
#             items = Item.objects.all()
#             return render(request, 'create_purchase.html', {
#                 'error': 'Please select a party.',
#                 'parties': parties,
#                 'items': items
#             })
#
#         party = get_object_or_404(Parties, id=party_id)
#         print("Selected party:", party)
#
#         purchase = Purchase.objects.create(party=party, total_amount=0, total_tax=0, total_discount=0)
#
#         # Retrieve hidden items and convert to list of integers
#         hidden_items = request.POST.get('hidden_items', '')
#         item_ids = [int(item_id) for item_id in hidden_items.split(',') if item_id.isdigit()]
#
#         quantities = request.POST.getlist('quantities')
#         prices = request.POST.getlist('prices')
#
#         # Combine item IDs with their respective quantities
#         items_and_quantities = [(item_id, quantity) for item_id, quantity in zip(item_ids, quantities) if
#                                 item_id and quantity]
#         items_and_prices = [(item_id, price) for item_id, price in zip(item_ids, prices) if
#                                 item_id and price]
#
#         print("Filtered items and quantities:", items_and_quantities)
#         print("Filtered items and prices:", items_and_prices)
#
#         if not items_and_quantities:
#             parties = Parties.objects.all()
#             items = Item.objects.all()
#             messages.error(request, 'Please select items and quantities.')  # Use messages framework
#
#             return render(request, 'create_purchase.html', {
#                 'error': 'Please select items and quantities.',
#                 'parties': parties,
#                 'items': items
#             })
#
#         total_amount = 0
#         total_tax = 0
#         total_discount = 0
#
#         # Process each valid item and its quantity
#         for item_id, quantity in items_and_quantities:
#             item = get_object_or_404(Item, id=item_id)  # Ensure item_id is an integer
#             quantity = int(quantity)
#
#             if item.stock_level < quantity:
#                 continue  # Skip this item and move to the next one
#
#             discount_amount = item.price * item.discount_rate / 100
#             discounted_price = item.price - discount_amount  # Price after discount
#             tax_amount = discounted_price * item.tax_rate / 100
#
#             print(f"Item: {item.name}, Price: {item.price}, Discount: {discount_amount}, Tax: {tax_amount}")
#
#             subtotal = (discounted_price + tax_amount) * quantity
#             total_amount += subtotal
#             total_tax += tax_amount * quantity
#             total_discount += discount_amount * quantity
#             PurchaseItem.objects.create(purchase=purchase, item=item, quantity=quantity)
#             # ... your existing sale logic ...
#             item.stock_level -= quantity  # Decrease stock level
#             item.save()
#
#
#
#         print("Total Amount:", total_amount)
#         print("Total Tax:", total_tax)
#         print("Total Discount:", total_discount)
#
#         # Update the bill totals
#         purchase.total_amount = total_amount
#         purchase.total_tax = total_tax
#         purchase.total_discount = total_discount
#         purchase.save()
#
#         return redirect(reverse('view_purchase', kwargs={'purchase_id': purchase.id}))
#
#     # GET request handling
#     parties = Parties.objects.all()
#     items = Item.objects.all()
#     return render(request, 'create_purchase.html', {'parties': parties, 'items': items})

# def create_purchase(request):
#     if request.method == "POST":
#         print("Received form data:", request.POST)
#
#         party_id = request.POST.get('party')
#
#         if not party_id:
#             # Handle missing party selection error
#             parties = Parties.objects.all()
#             items = Item.objects.all()
#             return render(request, 'create_purchase.html', {
#                 'error': 'Please select a party.',
#                 'parties': parties,
#                 'items': items
#             })
#
#         # Get the selected party
#         party = get_object_or_404(Parties, id=party_id)
#         print("Selected party:", party)
#
#         # Create a new Purchase record
#         purchase = Purchase.objects.create(
#             party=party,
#             total_amount=0,
#             total_tax=0,
#             total_discount=0
#         )
#
#         # Get hidden item IDs and validate
#         hidden_items = request.POST.get('hidden_items', '')
#         item_ids = [int(item_id) for item_id in hidden_items.split(',') if item_id.isdigit()]
#
#         # Retrieve corresponding input lists from POST request
#         quantities = request.POST.getlist('quantity[]')
#         prices = request.POST.getlist('price[]')
#         tax_rates = request.POST.getlist('tax[]')
#         discount_rates = request.POST.getlist('discount[]')
#
#         # Validate item selection and quantity entry
#         if not item_ids or not quantities:
#             parties = Parties.objects.all()
#             items = Item.objects.all()
#             messages.error(request, 'Please select items and quantities.')
#             return render(request, 'create_purchase.html', {
#                 'error': 'Please select items and quantities.',
#                 'parties': parties,
#                 'items': items
#             })
#
#         # Calculate totals and add entries to PurchaseItems table
#         total_amount = 0
#         total_tax = 0
#         total_discount = 0
#
#         for i, item_id in enumerate(item_ids):
#             item = get_object_or_404(Item, id=item_id)
#             quantity = int(quantities[i])
#             price = float(prices[i])
#             tax_rate = float(tax_rates[i])
#             discount_rate = float(discount_rates[i])
#
#             # Calculate discounted price and tax
#             discounted_price = price * (1 - discount_rate / 100)
#             total_price_with_tax = discounted_price * (1 + tax_rate / 100)
#
#             # Calculate subtotal and update totals
#             subtotal = total_price_with_tax * quantity
#             total_amount += subtotal
#             total_tax += (price * (tax_rate / 100)) * quantity
#             total_discount += (price * (discount_rate / 100)) * quantity
#
#             # Create a PurchaseItems record
#             PurchaseItem.objects.create(
#                 purchase=purchase,
#                 item=item,
#                 quantity=quantity,
#                 price=price,
#                 tax=tax_rate,
#                 discount=discount_rate,
#                 subtotal=subtotal
#             )
#
#         # Update the Purchase record with calculated totals
#         purchase.total_amount = total_amount
#         purchase.total_tax = total_tax
#         purchase.total_discount = total_discount
#         purchase.save()
#
#         messages.success(request, 'Purchase created successfully!')
#         return redirect('view_purchases')  # Redirect to view purchases page
#
#     # GET request: Render form with parties and items
#     parties = Parties.objects.all()
#     items = Item.objects.all()
#     return render(request, 'create_purchase.html', {'parties': parties, 'items': items})




def create_purchase(request):
    if request.method == "POST":
        print("Received form data:", request.POST)

        # Get the selected party
        party_id = request.POST.get('party')
        if not party_id:
            parties = Parties.objects.all()
            items = Item.objects.all()
            return render(request, 'create_purchase.html', {
                'error': 'Please select a party.',
                'parties': parties,
                'items': items
            })

        party = get_object_or_404(Parties, id=party_id)
        print("Selected party:", party)

        # Create a new Purchase record
        purchase = Purchase.objects.create(
            party=party,
            total_amount=0,
            total_tax=0,
            total_discount=0
        )

        # Get hidden item IDs and validate
        hidden_items = request.POST.get('hidden_items', '')
        item_ids = [int(item_id) for item_id in hidden_items.split(',') if item_id.isdigit()]

        # Retrieve corresponding input lists from POST request
        quantities = request.POST.getlist('quantities')
        prices = request.POST.getlist('price')
        tax_rates = request.POST.getlist('tax')
        discount_rates = request.POST.getlist('discount')

        # Validate item selection and quantity entry
        if not item_ids or not quantities:
            parties = Parties.objects.all()
            items = Item.objects.all()
            messages.error(request, 'Please select items and quantities.')
            return render(request, 'create_purchase.html', {
                'error': 'Please select items and quantities.',
                'parties': parties,
                'items': items
            })

        # Calculate totals and add entries to PurchaseItems table
        total_amount = 0
        total_tax = 0
        total_discount = 0

        for i, item_id in enumerate(item_ids):
            item = get_object_or_404(Item, id=item_id)
            quantity = int(quantities[i])
            price = float(prices[i])
            tax_rate = float(tax_rates[i])
            discount_rate = float(discount_rates[i])


            # Calculate discounted price and tax
            discounted_price = price * (1 - discount_rate / 100)
            total_price_with_tax = discounted_price * (1 + tax_rate / 100)
            #
            # # Calculate subtotal and update totals
            subtotal = total_price_with_tax * quantity
            total_amount += subtotal
            total_tax += (price * (tax_rate / 100)) * quantity
            total_discount += (price * (discount_rate / 100)) * quantity

            # Create a PurchaseItem record
            PurchaseItem.objects.create(
                purchase=purchase,
                item=item,
                quantity=quantity,
                price=price,
                tax=tax_rate,
                discount=discount_rate,
                subtotal=subtotal
            )

        # Update the Purchase record with calculated totals
        purchase.total_amount = total_amount
        purchase.total_tax = total_tax
        purchase.total_discount = total_discount
        purchase.save()

        messages.success(request, 'Purchase created successfully!')
        return redirect('view_purchases')  # Redirect to view purchases page

    # GET request: Render form with parties and items
    parties = Parties.objects.all()
    items = Item.objects.all()
    return render(request, 'create_purchase.html', {'parties': parties, 'items': items})

def view_purchase(request, purchase_id):
        purchase = get_object_or_404(Purchase, id=purchase_id)
        purchase_items = PurchaseItem.objects.filter(purchase=purchase)  # Get all items for the bill

        context = {
            'purchase': purchase,
            'purchase_items': purchase_items,
        }
        return render(request, 'create_purchase.html', context)



def purchase_list(request):
    purchases = Purchase.objects.all()
    return render(request, 'purchase_list.html', {'purchases': purchases})




def download_purchase_pdf(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    purchase_items = PurchaseItem.objects.filter(purchase=purchase)

    template_path = 'purchase_pdf_template.html'  # Make sure you have this template created
    context = {'purchase': purchase, 'purchase_items': purchase_items}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="purchase_{purchase_id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    # Generate PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error creating PDF', status=400)

    return response

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



def sales_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initialize sales queryset
    sales = Bill.objects.all()

    if start_date and end_date:
        try:
            # Convert to datetime objects
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)

            # Adjust the end date to include the whole day
            end_date = timezone.datetime.combine(end_date, timezone.datetime.max.time())

            # Filter based on the date range
            sales = sales.filter(created_at__range=[start_date, end_date])

            # Debug output to check the filtered sales
            print(f"Filtered Sales: {sales}")

        except ValueError:
            # Handle the case where the date format is incorrect
            sales = sales.none()  # No sales if date format is invalid
            print("Invalid date format received.")

    # Calculate total sales
    total_sales = sum(sale.total_amount for sale in sales)

    context = {
        'sales': sales,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
    }
    return render(request, 'sales_report.html', context)


def purchase_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initialize sales queryset
    purchases = Purchase.objects.all()

    if start_date and end_date:
        try:
            # Convert to datetime objects
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)

            # Adjust the end date to include the whole day
            end_date = timezone.datetime.combine(end_date, timezone.datetime.max.time())

            # Filter based on the date range
            purchase = purchases.filter(created_at__range=[start_date, end_date])

            # Debug output to check the filtered sales
            print(f"Filtered purchases: {purchase}")

        except ValueError:
            # Handle the case where the date format is incorrect
            purchase = purchase.none()  # No sales if date format is invalid
            print("Invalid date format received.")

    # Calculate total sales
    total_purchase = sum(purchase.total_amount for purchase in purchases)

    context = {
        'purchases': purchases,
        'start_date': start_date,
        'end_date': end_date,
        'total_purchase': total_purchase,
    }
    return render(request, 'purchase_report.html', context)


def download_sales_report(request):
    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    writer.writerow(['Party', 'Total Amount', 'Total Tax', 'Total Discount', 'Date'])

    # Fetch all sales records
    sales = Bill.objects.all()

    for sale in sales:
        party_name = sale.party.name if sale.party else 'N/A'  # Handle cases where party might be None

        # Calculate the total amount based on related BillItems
        total_amount = sum(item.quantity * item.item.price for item in
                           sale.bill_items.all())  # Adjust as per your price calculation logic
        total_tax = sale.total_tax or 0  # Default to 0 if None
        total_discount = sale.total_discount or 0  # Default to 0 if None
        created_at = sale.created_at.strftime('%Y-%m-%d %H:%M:%S') if sale.created_at else 'N/A'  # Format datetime

        writer.writerow([party_name, total_amount, total_tax, total_discount, created_at])

    return response


#
#     return response
def report(request):
    return render(request, 'reports.html')


def sales_report_view(request):
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    bills = Bill.objects.all()  # Default to all bills if no filters applied

    try:
        if start_date and end_date:
            # Parse the date strings
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

            # Filter bills within the date range (inclusive)
            bills = Bill.objects.filter(created_at__range=[start_date, end_date])

        # Calculate total sales
        total_sales = bills.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0

    except ValueError:
        # Handle invalid date input gracefully
        total_sales = 0
        start_date = None
        end_date = None

    context = {
        'total_sales': total_sales,
        'bills': bills,  # Pass filtered bills to the context
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'sales_report.html', context)



def purchase_report_view(request):
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        purchases = Purchase.objects.filter(created_at__range=[start_date, end_date])
        total_purchases = purchases.aggregate(total_purchases=Sum('total_amount'))['total_purchases'] or 0
    else:
        purchases = Purchase.objects.all()
        total_purchases = purchases.aggregate(total_purchases=Sum('total_amount'))['total_purchases'] or 0

    context = {
        'total_purchases': total_purchases,
        'start_date': start_date,
        'end_date': end_date,
        'purchases': purchases
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


def filter_parties(request):
    search_term = request.GET.get('q', '')
    parties = Parties.objects.filter(name__icontains=search_term).values('id', 'name')
    return JsonResponse(list(parties), safe=False)

def filter_items(request):
    search_term = request.GET.get('q', '')
    items = Item.objects.filter(name__icontains=search_term).values('id', 'name', 'price', 'tax_rate', 'discount_rate')
    return JsonResponse(list(items), safe=False)

def add_purchase(request):
    if request.method == 'POST':
        # Handle form data and save to the purchase and purchase_items tables
        ...

def check_low_stock(request):
    low_stock_items = Item.objects.filter(stock_level__lt=F('low_stock_threshold'))
    return render(request, 'low_stock_alert.html', {'low_stock_items': low_stock_items})


def profit_loss_report(request):
    # Fetch total sales and total purchases
    total_sales = Bill.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_purchases = Purchase.objects.aggregate(total=Sum('total_amount'))['total'] or 0

    profit = total_sales - total_purchases
    loss = abs(profit) if profit < 0 else 0

    context = {
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'profit': profit if profit > 0 else 0,
        'loss': loss,
    }
    return render(request, 'profit_loss_report.html', context)


