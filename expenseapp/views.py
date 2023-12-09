from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from .models import Expense
from .forms import ExpenseForm, ReceiptForm
from django.views import View
from dateutil.parser import parse
import os
from django.conf import settings
from dateutil.parser import ParserError
from veryfi import Client
import json
from django.contrib import messages
from django.db.models import Sum
from dotenv import load_dotenv

#https://docs.djangoproject.com/en/4.2/intro/tutorial01/.
# this is where my views are created
# Display Home Page
def Welcome(request):
    return render(request, "welcome.html")

#loggedIn User Dashboard
class AppView(LoginRequiredMixin, TemplateView):
    template_name = "user_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date and end_date:
            # Filter data based on the selected date range
            expenses= Expense.objects.filter(date__range=[start_date, end_date], user=self.request.user)
            category_breakdown = Expense.objects.filter(date__range=[start_date, end_date], user=self.request.user).values('category')\
                            .annotate(total=Sum('amount'))
        else:
            # Default to all data if no date range is selected
            expenses= Expense.objects.filter(user=self.request.user)
            category_breakdown = Expense.objects.filter(date__range=[start_date, end_date], user=self.request.user).values('category')\
                            .annotate(total=Sum('amount'))

        #pass the user expenses to context
        context['expenses'] = expenses
         
          #get all the expense categories from and a summation of all their amounts of expenses
        context['category_breakdown'] = category_breakdown
        return context
    
    


#View for rendering and processing 
# manual expense entry
class ManualExpenseView(LoginRequiredMixin, CreateView):
    template_name = "manual_expense_entry.html"
    form_class = ExpenseForm
    success_url = reverse_lazy("expense_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.receipt_image_path = self.request.POST.get('receipt_image_path')
        messages.success(self.request, 'Expense entry was successfully added!')
        return super().form_valid(form)


#View for rendering and processing 
# manual expense entry
class ReceiptExpenseAddView(LoginRequiredMixin, View):

   
   def post(self, request):
       
       store_name = request.POST.get('store_name')
       amount = request.POST.get('amount')
       date = request.POST.get('date')
       category = request.POST.get('category')

       exepnse_transactions = Expense(user=request.user, store_name= store_name, amount = amount, \
                                               date = date, category = category)

       exepnse_transactions.save()

       messages.success(request, 'Expense Transactions  successfully Added!')

       return redirect("expense_list")


#View For Extracting, Preprocessing 
# And Extracting Expense Data From Receipts
class ReceiptExpenseView(TemplateView):
    #display receipt expense form
    template_name = "receipt_expense_view.html"
    
#Expense List View
class ExpenseListView(LoginRequiredMixin, ListView):

    model = Expense
    template_name = "expense_list_view.html"

    def get_queryset(self):
        expense_query_set = super().get_queryset()
        return expense_query_set.filter(user = self.request.user)

    

class ReceiptProcessView(View):
    template_name = 'process_receipt.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Process the uploaded receipt image
        if 'receipt_image' in request.FILES:
                receipt_image = request.FILES['receipt_image']

                #Upload the receipt image to the media/receipts 
                #directory using instructions from
                #https://docs.djangoproject.com/en/4.2/topics/http/file-uploads/

                receipt_upload_path = os.path.join(settings.MEDIA_ROOT, 'receipts', receipt_image.name)
                with open(receipt_upload_path, 'wb+') as destination:
                    for chunk in receipt_image.chunks():
                     if  destination.write(chunk):
                         #save the uploaded receipt relative path
                         receipt_relative_path = os.path.relpath(receipt_upload_path, settings.MEDIA_ROOT)
            


                # https://hub.veryfi.com/api/
                 # Load Enviromental Variables 
                load_dotenv()
                # get your keys here: https://hub.veryfi.com/api/
                client_id = os.getenv('VERYFI_CLIENT_ID')
                client_secret = os.getenv('VERYFI_CLIENT_SECRET')
                username = os.getenv('VERYFI_USERNAME')
                api_key = os.getenv('VERYFI_API_KEY')

                veryfi_client = Client(client_id, client_secret, username, api_key)

                categories = ['Grocery', 'Utilities', 'Travel']
                  
                # submits document for processing (takes 3-5 seconds to get response)
                document_json = veryfi_client.process_document(receipt_upload_path, categories=categories)
                data = document_json

                vendor_name = data['vendor']['name']
                category = data['category']
                date_of_transaction = data['date']
                total_amount = data['total']

                try:
                    stripped_date = parse(date_of_transaction, parserinfo=None)
                except (TypeError, ParserError):
                    stripped_date  = datetime.today()
                
                context = { "transaction_date": stripped_date, "store_name": vendor_name,
                            "amount": total_amount, "receipt_upload_path": receipt_relative_path, "category": category }
                return render(request, 'post_receipt_expense.html', context)


#View for updating expense
class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    template_name = "manual_expense_entry.html"
    form_class = ExpenseForm
    success_url = reverse_lazy("expense_list")
   
   #Override form_valid method to return success update message
    def form_valid(self, form):
        messages.success(self.request, 'Expense updated successfully!!!.')
        return super().form_valid(form)
    
     #view for deleting expenses
class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = "confirm_delete_expense.html"  
    success_url = reverse_lazy("expense_list")
    success_message = 'Expense deleted successfully!!!'
       
      
