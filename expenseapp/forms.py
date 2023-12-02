from django import forms

from .models import Expense

#setting up the form fields
#https://www.geeksforgeeks.org/multiplechoicefield-django-forms/


CATEGORIES_CHOICES = ( 
    ("foodandgroceries", "Food and Groceries"), 
    ("rent", "Rent"), 
    ("utility", "Utility"),  
    ("refund", "Refund"), 
    ("schoollunch", "School Lunch"),
    ("giftanddonations", "Gifts and Donations" ),
    ("clothingandshoes", "Clothing and Shoes" ),
    ("mealsandentertainment", "Meals and Entertainment" ),
    

) 

class ExpenseForm(forms.ModelForm):
    store_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(max_digits=20, decimal_places=3, widget=forms.NumberInput(attrs={'class': 'form-control'} ))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    category = forms.ChoiceField(choices=CATEGORIES_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}), required=False)

    class Meta:
        model = Expense
        fields = ['store_name', 'amount', 'date', 'category']



class ReceiptForm(forms.ModelForm):
    store_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(max_digits=20, decimal_places=3, widget=forms.NumberInput(attrs={'class': 'form-control'} ))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    category = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-select'}), required=False)

    class Meta:
        model = Expense
        fields = ['store_name', 'amount', 'date', 'category']
