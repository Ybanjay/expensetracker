from django import forms

from .models import Expense

#setting up the form fields
#https://www.geeksforgeeks.org/multiplechoicefield-django-forms/

CATEGORIES_CHOICES = ( 
    ("groceries", "Groceries"), 
    ("rent", "Rent"), 
    ("utility", "Utility"),  
    ("refund", "Refund"), 
    ("schoollunch", "School Lunch"),
    ("giftanddonations", "Gifts and Donations" ),

) 
class ExpenseForm(forms.ModelForm):
    item = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(max_digits=20, decimal_places=3, widget=forms.NumberInput(attrs={'class': 'form-control'} ))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    category = forms.ChoiceField(choices=CATEGORIES_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}), required=False)

    class Meta:
        model = Expense
        fields = ['item', 'amount', 'date', 'category']

