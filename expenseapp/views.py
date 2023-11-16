from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from .models import Expense
from .forms import ExpenseForm
from django.views import View
import numpy as np
import cv2
import pytesseract
import spacy
from datetime import datetime
from dateutil.parser import parse
import re
import os
from django.conf import settings
from dateutil.parser import ParserError
from veryfi import Client
import json
from django.contrib import messages

# Create your views here.
# Display Home Page
def Welcome(request):
    return render(request, "welcome.html")

#loggedIn User Dashboard
class AppView(LoginRequiredMixin, TemplateView):
    template_name = "user_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['expenses'] = Expense.objects.filter(user=self.request.user)
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


#View For Extracting, Preprocessing 
# And Extracting Expense Data From Receipts
class ReceiptExpenseView(TemplateView):
    #display receipt expense form
    template_name = "receipt_expense_view.html"
    
#Expense List View
class ExpenseListView(LoginRequiredMixin, ListView):

    model = Expense
    template_name = "expense_list_view.html"
    

class ReceiptProcessView(View):
    template_name = 'process_receipt.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Process the uploaded receipt image
        if 'receipt_image' in request.FILES:
                receipt_image = request.FILES['receipt_image']

                 #Read Image Using OpenCV2
                img = cv2.imdecode(np.frombuffer(receipt_image.read(), np.uint8), -1)

                #Upload the receipt image to the media/receipts 
                #directory with using instructions from
                #https://docs.djangoproject.com/en/4.2/topics/http/file-uploads/

                receipt_upload_path = os.path.join(settings.MEDIA_ROOT, 'receipts', receipt_image.name)
                with open(receipt_upload_path, 'wb+') as destination:
                    for chunk in receipt_image.chunks():
                     if  destination.write(chunk):
                         #save the uploaded receipt relative path
                         receipt_relative_path = os.path.relpath(receipt_upload_path, settings.MEDIA_ROOT)
            


                # https://hub.veryfi.com/api/
                client_id = 'vrfZ59w40O08opIU5szMZo3fGUPVjLZ59mMPVfx'
                client_secret = 'aMVpxdo4Wd6DS97Bpcfp1ERkKgFoRdIlvKEOWRrjxIv23T5VaY3k2JWrZOTr3xXY4oAddejMUAojwBgI0Pd8DyzAFv9d4udoINLJwchXc9I4BmKGf7ZO90kEmzOXbk76'
                username = 'softerboom'
                api_key = 'c43a0fb9f07383c6db2357056afa2405'

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
                            "amount": total_amount, "receipt_upload_path": receipt_relative_path }
                return render(request, 'post_receipt_expense.html', context)

