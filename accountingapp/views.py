import calendar
import csv
from datetime import datetime
import logging
from django.contrib.auth.decorators import login_required
from django.contrib import auth, messages
from django.db.models import Sum, Q, F
from django.db.models.functions import TruncMonth, ExtractYear, ExtractMonth, ExtractDay
from django.http import HttpResponse, JsonResponse, request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.template.loader import get_template
from django.urls import reverse
from .forms import ItemForm, CategoryForm, PartyForm, CustomUserCreationForm, PurchaseForm, BillForm
from .models import Item, Category, Parties,  Purchase, PurchaseItem, BillItem, Bill
from xhtml2pdf import pisa

# Home view
def home(request):
    return render(request, 'home.html')

@login_required
def dashboard(request):

    return render(request, 'base.html')

@login_required
def dashboard_view(request):
    # Aggregate data by day instead of month and year
    sales = Bill.objects.filter(user=request.user).annotate(
        year=ExtractYear('created_at'),
        month=ExtractMonth('created_at'),
        day=ExtractDay('created_at')
    ).values('year', 'month', 'day').annotate(total=Sum('total_amount'))

    purchases = Purchase.objects.filter(user=request.user).annotate(
        year=ExtractYear('created_at'),
        month=ExtractMonth('created_at'),
        day=ExtractDay('created_at')
    ).values('year', 'month', 'day').annotate(total=Sum('total_amount'))

    # Process data and prepare day-based labels
    sales_data = {(sale['year'], sale['month'], sale['day']): float(sale['total']) for sale in sales}
    purchase_data = {(purchase['year'], purchase['month'], purchase['day']): float(purchase['total']) for purchase in
                     purchases}

    # Generate a sorted list of days for the labels
    days = sorted(set(sales_data.keys()).union(purchase_data.keys()))

    # Prepare data for sales, purchases, and profit/loss on a day-by-day basis
    sales_data_list = []
    purchase_data_list = []
    profit_loss_data = []
    labels = []

    for day in days:
        year, month, day_num = day
        sales_total = sales_data.get(day, 0)
        purchase_total = purchase_data.get(day, 0)

        # Append to lists
        sales_data_list.append(sales_total)
        purchase_data_list.append(purchase_total)
        profit_loss_data.append(sales_total - purchase_total)

        # Label format: "Month Day, Year"
        labels.append(f"{calendar.month_name[month]} {day_num}, {year}")

    context = {
        'sales_data': sales_data_list,
        'purchase_data': purchase_data_list,
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

@login_required
def item_list(request):
    search_query = request.GET.get('search', '')  # Get the search query from the request
    if search_query:
        items = Item.objects.filter(user=request.user,name__icontains=search_query)  # Filter items based on the search query
    else:
        items = Item.objects.filter(user=request.user)  # If no search, display all items

    return render(request, 'item_list.html', {'items': items})

@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            return redirect('item_list')
    else:
        form = ItemForm()

    return render(request, 'add_item.html', {'form': form})



        # Redirect back to the purchase form with the new item's ID


# View to update item
@login_required
def update_item(request, pk):
    item = get_object_or_404(Item, pk=pk,user=request.user)
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
    item = get_object_or_404(Item, pk=pk,user=request.user)
    if request.method == 'POST':
        item.delete()
        return redirect('item_list')
    return render(request, 'delete_item.html', {'item': item})

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)  # Get the form instance without saving to the database yet
            category.user = request.user  # Assign the logged-in user to the category
            category.save()  # Save the category to the database
            return redirect('category_list')  # Redirect to the category list page after saving
    else:
        form = CategoryForm()
    return render(request, 'add_category.html', {'form': form})

@login_required
def update_category(request, pk):
    category = get_object_or_404(Category, pk=pk,user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'update_category.html', {'form': form})

@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk,user=request.user)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')

    return render(request, 'delete_category.html', {'category': category})

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)  # Retrieve all categories from the database
    return render(request, 'category_list.html', {'categories': categories})


@login_required
def party_list(request):
    # parties = Parties.objects.all()
    # Assuming your model is named Parties

        search_query = request.GET.get('search', '')  # Get search query from the request
        if search_query:
            # Filter parties by name or phone number matching the search query
            parties = Parties.objects.filter(name__icontains=search_query) | Parties.objects.filter(
                phone_number__icontains=search_query,user=request.user)
        else:
            parties = Parties.objects.filter(user=request.user)  # If no search, display all parties


        return render(request, 'party_list.html', {'parties': parties})

@login_required
def add_party(request):
    if request.method == 'POST':
        form = PartyForm(request.POST)
        if form.is_valid():
            party = form.save(commit=False)  # Save form without committing to the database yet
            party.user = request.user  # Assign the logged-in user to the party
            party.save()
        return redirect('party_list')
    else:
        form = PartyForm()
    return render(request, 'add_party.html', {'form': form})

# Update a party
@login_required
def update_party(request, pk):
    party = get_object_or_404(Parties, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PartyForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            return redirect('party_list')
    else:
        form = PartyForm(instance=party)
    return render(request, 'update_party.html', {'form': form})

# Delete a party
@login_required
def delete_party(request, pk):
    party = get_object_or_404(Parties, pk=pk,user=request.user)
    if request.method == 'POST':
        party.delete()
        return redirect('party_list')
    return render(request, 'delete_party.html', {'party': party})

logger = logging.getLogger(__name__)

@login_required
def create_bill(request):
    if request.method == "POST":
        print("Received form data:", request.POST)

        party_id = request.POST.get('party')
        if not party_id:
            parties = Parties.objects.filter(user=request.user)
            items = Item.objects.filter(user=request.user)
            return render(request, 'create_bill.html', {
                'error': 'Please select a party.',
                'parties': parties,
                'items': items
            })

        party = get_object_or_404(Parties, id=party_id,user=request.user)
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
            parties = Parties.objects.filter(user=request.user)
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
            BillItem.objects.create(
                bill=bill,
                item=item,
                quantity=quantity,
                price = item.price,  # Save the item's price
                tax_rate = item.tax_rate,  # Save the item's tax rate
                discount_rate = item.discount_rate,  # Save the item's discount rate
                subtotal = subtotal
            )
            # ... your existing sale logic ...
            item.stock_level -= quantity  # Decrease stock level
            item.save()

        print("Total Amount:", total_amount)
        print("Total Tax:", total_tax)
        print("Total Discount:", total_discount)
        print("subtotal:", subtotal)

        # Update the bill totals
        bill.total_amount = total_amount
        bill.total_tax = total_tax
        bill.total_discount = total_discount
        bill.save()

        return redirect(reverse('view_bill', kwargs={'bill_id': bill.id}))
    # GET request handling
    parties = Parties.objects.filter(user=request.user)
    items = Item.objects.filter(user=request.user)
    return render(request, 'create_bill.html', {'parties': parties, 'items': items})

@login_required
def view_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    bill_items = BillItem.objects.filter(bill=bill)  # Get all items for the bill

    context = {
        'bill': bill,
        'bill_items': bill_items,
    }
    return render(request, 'bill_pdf_template.html', context)

#  Generate and download PDF
@login_required
def download_bill_pdf(request,bill_id):
    bill = Bill.objects.get(id=bill_id,user=request.user)
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

@login_required
def edit_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id,user=request.user)
    bill_items = BillItem.objects.filter(bill=bill)

    if request.method == "POST":
        # Get the additional item details from the form
        item_id = request.POST.get('item')
        quantity = request.POST.get('quantity')

        if not item_id or not quantity:
            messages.error(request, 'Please select an item and a quantity.')
            return redirect('edit_bill', bill_id=bill.id)

        item = get_object_or_404(Item, id=item_id)
        quantity = int(quantity)

        if item.stock_level < quantity:
            messages.error(request, f'Item "{item.name}" is out of stock, please select another item.')
            return redirect('edit_bill', bill_id=bill.id)

        # Calculate price, tax, and discount
        discount_amount = item.price * item.discount_rate / 100
        discounted_price = item.price - discount_amount
        tax_amount = discounted_price * item.tax_rate / 100

        subtotal = (discounted_price + tax_amount) * quantity

        # Create a new BillItem for the additional item
        BillItem.objects.create(bill=bill,
                                item=item,
                                quantity=quantity,
                                price=item.price,
                                tax_rate=item.tax_rate,
                                discount_rate=item.discount_rate,
                                subtotal=subtotal
                                )

        # Update the stock level
        item.stock_level -= quantity
        item.save()

        # Update the bill totals
        bill.total_amount += subtotal
        bill.total_tax += tax_amount * quantity
        bill.total_discount += discount_amount * quantity
        bill.save()

        messages.success(request, 'Bill updated successfully.')
        return redirect('view_bill', bill_id=bill.id)

    # GET request handling
    parties = Parties.objects.filter(user=request.user)
    items = Item.objects.filter(user=request.user)
    return render(request, 'edit_bill.html', {
        'bill': bill,
        'bill_items': bill_items,
        'parties': parties,
        'items': items,
    })

#
@login_required
def create_purchase(request):
    if request.method == "POST":
        print("Received form data:", request.POST)

        # Get the selected party
        party_id = request.POST.get('party')
        if not party_id:
            parties = Parties.objects.filter(user=request.user)
            items = Item.objects.filter(user=request.user)
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
        print("Hidden items received:", hidden_items)
        item_ids = [int(item_id) for item_id in hidden_items.split(',') if item_id.isdigit()]

        # Retrieve corresponding input lists from POST request
        quantities = request.POST.getlist('quantities')
        prices = request.POST.getlist('price')
        tax_rates = request.POST.getlist('tax')
        discount_rates = request.POST.getlist('discount')

        items_and_details = [(item_id, quantity, pr, dis, tx) for item_id, quantity, pr, dis, tx in zip(item_ids, quantities, prices, discount_rates, tax_rates) if item_id and quantity and pr and dis and tx]


        print("Filtered items and details:", items_and_details)

        # Validate item selection and quantity entry
        if not items_and_details:
            parties = Parties.objects.filter(user=request.user)
            items = Item.objects.filter(user=request.user)
            messages.error(request, 'Please select items and .')
            return render(request, 'create_purchase.html', {
                'error': 'Please select items and .',
                'parties': parties,
                'items': items
            })

        # Calculate totals and add entries to PurchaseItems table
        total_amount = 0
        total_tax = 0
        total_discount = 0

        for item_id,quantity,pr,dis,tx in items_and_details:
            item = get_object_or_404(Item, id=item_id)
            quantity = int(quantity)
            price = float(pr)
            tax_rate = float(tx)
            discount_rate = float(dis)


            # Calculate discounted price and tax
            discount_amount = item.price * item.discount_rate / 100
            discounted_price = item.price - discount_amount  # Price after discount
            tax_amount = discounted_price * item.tax_rate / 100

            print(f"Item: {item.name}, Price: {item.price}, Discount: {discount_amount}, Tax: {tax_amount}")


            #
            # # Calculate subtotal and update totals
            subtotal = (discounted_price + tax_amount) * quantity
            total_amount += subtotal
            total_tax += tax_amount * quantity
            total_discount += discount_amount * quantity

            # Create a PurchaseItem record
            PurchaseItem.objects.create(
                purchase=purchase,
                item=item,
                quantity=quantity,
                price=price,
                tax_rate=tax_rate,
                discount_rate=discount_rate
            )

            print("Total Amount:", total_amount)
            print("Total Tax:", total_tax)
            print("Total Discount:", total_discount)

        # Update the Purchase record with calculated totals
        purchase.total_amount = total_amount
        purchase.total_tax = total_tax
        purchase.total_discount = total_discount
        purchase.save()

        messages.success(request, 'Purchase created successfully!')
        return redirect('purchase_success')  # Redirect to view purchases page

    # GET request: Render form with parties and items
    parties = Parties.objects.filter(user=request.user)
    items = Item.objects.filter(user=request.user)
    selected_item_id = request.GET.get('item_id')
    return render(request, 'create_purchase.html', {'parties': parties, 'items': items, 'selected_item_id': selected_item_id})

@login_required
def purchase_success(request):
    return render(request, 'purchase_success.html',{'purchase success':purchase_success})





#     return response
@login_required
def report(request):
    return render(request, 'reports.html')

@login_required
def sales_report_view(request):
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    bills = Bill.objects.filter(user=request.user)  # Default to all bills if no filters applied

    try:
        if start_date and end_date:
            # Parse the date strings
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

            # Filter bills within the date range (inclusive)
            bills = Bill.objects.filter(created_at__range=[start_date, end_date],user=request.user)

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


@login_required
def purchase_report_view(request):
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    purchases = Purchase.objects.filter(user=request.user)  # Default to all bills if no filters applied

    try:
        if start_date and end_date:
            # Parse the date strings
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

            # Filter bills within the date range (inclusive)
            purchases = Purchase.objects.filter(created_at__range=[start_date, end_date],user=request.user)

        # Calculate total sales
        total_purchases = purchases.aggregate(total_purchases=Sum('total_amount'))['total_purchases'] or 0

    except ValueError:
        # Handle invalid date input gracefully
        total_purchases = 0
        start_date = None
        end_date = None

    context = {
        'total_purchases': total_purchases,
        'purchases': purchases,  # Pass filtered bills to the context
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'purchase_report.html', context)


@login_required
def search_party(request):
    query = request.GET.get('q', '')
    if query:
        parties = Parties.objects.filter(name__icontains=query,user=request.user)
    else:
        parties = Parties.objects.none()

    results = [{'id': party.id, 'name': party.name} for party in parties]
    return JsonResponse({'results': results})


# Item search view
@login_required
def search_item(request):
    query = request.GET.get('q', '')
    if query:
        items = Item.objects.filter(name__icontains=query,user=request.user)
    else:
        items = Item.objects.none()

    results = [{'id': item.id, 'name': item.name, 'price': item.price} for item in items]
    return JsonResponse({'results': results})

@login_required
def filter_parties(request):
    search_term = request.GET.get('q', '')
    parties = Parties.objects.filter(name__icontains=search_term,user=request.user).values('id', 'name')
    return JsonResponse(list(parties), safe=False)

@login_required
def filter_items(request):
    search_term = request.GET.get('q', '')
    items = Item.objects.filter(name__icontains=search_term,user=request.user).values('id', 'name', 'price', 'tax_rate', 'discount_rate')
    return JsonResponse(list(items), safe=False)

@login_required
def check_low_stock(request):
    low_stock_items = Item.objects.filter(stock_level__lt=F('low_stock_threshold'),user=request.user)
    return render(request, 'low_stock_alert.html', {'low_stock_items': low_stock_items})


@login_required
def profit_loss_report(request):
    # Group sales and purchases by month and year
    monthly_sales = (
        Bill.objects.filter(user=request.user)
        .annotate(year=ExtractYear('created_at'), month=ExtractMonth('created_at'))
        .values('year', 'month')
        .annotate(total=Sum('total_amount'))
        .order_by('year', 'month')
    )

    monthly_purchases = (
        Purchase.objects.filter(user=request.user)
        .annotate(year=ExtractYear('created_at'), month=ExtractMonth('created_at'))
        .values('year', 'month')
        .annotate(total=Sum('total_amount'))
        .order_by('year', 'month')
    )

    # Prepare a dictionary to hold profit/loss data for each month
    profit_loss_data = {}
    for sale in monthly_sales:
        year_month = (sale['year'], sale['month'])
        profit_loss_data[year_month] = {
            'sales': sale['total'],
            'purchases': 0,
            'profit': 0,
            'loss': 0
        }

    for purchase in monthly_purchases:
        year_month = (purchase['year'], purchase['month'])
        if year_month not in profit_loss_data:
            profit_loss_data[year_month] = {
                'sales': 0,
                'purchases': purchase['total'],
                'profit': 0,
                'loss': 0
            }
        else:
            profit_loss_data[year_month]['purchases'] = purchase['total']

    # Calculate profit/loss for each month
    for year_month, data in profit_loss_data.items():
        sales = data['sales']
        purchases = data['purchases']
        profit = sales - purchases
        data['profit'] = profit if profit > 0 else 0
        data['loss'] = abs(profit) if profit < 0 else 0

    # Convert year and month into readable labels
    report_data = [
        {
            'month': f"{calendar.month_name[month]} {year}",
            'sales': data['sales'],
            'purchases': data['purchases'],
            'profit': data['profit'],
            'loss': data['loss']
        }
        for (year, month), data in sorted(profit_loss_data.items())
    ]

    context = {
        'report_data': report_data,
    }
    return render(request, 'profit_loss_report.html', context)
