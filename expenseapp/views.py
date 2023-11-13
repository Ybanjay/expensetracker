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

                # Read and extract data from image
                # following instructions from the following sources
                # 1) https://pypi.org/project/pytesseract/
                # 2) https://nanonets.com/blog/how-to-extract-data-from-invoices-using-python/amp/
                # 3) https://pyimagesearch.com/2021/10/27/automatically-ocring-receipts-and-scans/
                # 4) https://www.kaggle.com/code/dmitryyemelyanov/receipt-ocr-part-1-image-segmentation-by-opencv


                #Resize Image
                resized_image = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

                #convert the image to grayscale 
                # for better extraction from OCR 
                gray_scale = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)


                #threshold_image = cv2.threshold(gray_scale, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                gaussian_blur = cv2.GaussianBlur(gray_scale, (5, 5), 0)

                #set Pytesseract
                pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract"
                
                custom_config = r'--oem 3 --psm 6'
                ocr_text = pytesseract.image_to_string(gaussian_blur, lang="eng", config="custom_config")

                

                #Normalize Date: find the receipt date patter with regular expression
                # and replace all instance of it with a more recognizable format by spacy

                # Define a regular expression pattern to find dates in the format "29/9/23 00:00:00"
                date_pattern = re.compile(r'\b(\d{1,2}/\d{1,2}/\d{2} \d{2}:\d{2}:\d{2})\b')
                # Find all matches in the text
                matches = date_pattern.findall(ocr_text)

                # Convert each matched date to a standard format
                for match in matches:
                    converted_date = datetime.strptime(match, "%d/%m/%y %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
                    ocr_text = ocr_text.replace(match, converted_date)


                nlp = spacy.load('en_core_web_sm')
                doc = nlp(ocr_text)

                organization = None
                total_amount = None
                trans_date = None



                for ent in doc.ents:
                    if ent.label_ == "ORG" and organization is None:
                        organization = ent.text.strip()

                    elif ent.label_ == "DATE":
                        trans_date  = ent.text.strip()


                #post process Spacy Total Amount
                for token in doc:
                    # Look for keywords that suggest total amount in relation to MONEY entities
                    if token.text.lower() in ["total", "due", "balance"]:
                        for child in token.children:
                            if child.ent_type_ == "MONEY" and total_amount == None:
                                total_amount = float(child.text.replace("£", ""))  
                                break

                try:
                    stripped_date = parse(trans_date, parserinfo=None)
                except (TypeError, ParserError):
                    stripped_date  = datetime.today()

                if total_amount is None:
                    total_amount = 0.00
                
                context = {'extracted_text': ocr_text, "transaction_date": stripped_date, 
                           "company": organization, "amount": total_amount,
                             "receipt_upload_path": receipt_relative_path }
                return render(request, 'post_receipt_expense.html', context)

        return render(request, self.template_name)

