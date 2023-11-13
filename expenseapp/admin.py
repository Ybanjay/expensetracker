from django.contrib import admin
from .models import Expense

# Register your models here.
admin.site.site_header = "Expense App Admin"
admin.site.site_title = "Expense App Admin Area"
admin.site.index_title = "Welcome to Expense App Admin Area"
admin.site.register(Expense)