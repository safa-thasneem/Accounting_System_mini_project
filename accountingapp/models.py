from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    place = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.email


class Category(models.Model):
    name = models.CharField(max_length=100)  # Field for category name
    created_at = models.DateTimeField(auto_now_add=True)  # Field to store when the category was created

    def __str__(self):
        return self.name


class Parties(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return self.name



class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    # Tax Fields
    has_tax = models.BooleanField(default=False)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Changed field name

    # Discount Fields
    has_discount = models.BooleanField(default=False)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Changed field name
    stock_level = models.IntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)  # Set a threshold for low stock
    created_at = models.DateTimeField(auto_now_add=True)



class Bill(models.Model):
    party = models.ForeignKey(Parties, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)



class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)  # Changed field name
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)  # Changed field name




class Purchase(models.Model):
    party = models.ForeignKey(Parties, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)  # Changed field name
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)  # Changed field name

