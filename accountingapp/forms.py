import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User, Profile, Item, Category, Parties, Purchase, Bill, BillItem


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email address', widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Username',
            'email': 'Email address',
            'password1': 'Password',
            'password2': 'Password confirmation',

        }
        help_texts = {
            'email': 'Enter email',
            'password1': None,  # Removes password validation help text
            'password2': 'Enter the same password as before, for verification',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
        class Meta:
            model = Profile
            fields = ['phone_number', 'place']

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'price', 'category', 'has_tax', 'tax_rate', 'has_discount', 'discount_rate', 'stock_level']




class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class PartyForm(forms.ModelForm):
    class Meta:
        model = Parties
        fields = ['name', 'phone_number']

        def clean_name(self):
            name = self.cleaned_data.get('name')
            if not re.match("^[a-zA-Z\s]+$", name):
                raise ValidationError("Name can only contain alphabetic characters and spaces.")
            return name

        def clean_phone_number(self):
            phone_number = self.cleaned_data.get('phone_number')
            if not phone_number.isdigit():
                raise ValidationError("Phone number must contain only numeric digits.")
            return phone_number


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['party']  # Include fields from Bill model

class BillItemForm(forms.ModelForm):
    class Meta:
        model = BillItem
        fields = ['item', 'quantity']


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['party', 'total_amount', 'total_tax', 'total_discount']  # Add any other necessary fields

class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = BillItem
        fields = ['item', 'quantity']






