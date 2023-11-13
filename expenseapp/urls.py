
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import ManualExpenseView, AppView, ExpenseListView, ReceiptProcessView
from . import views



urlpatterns = [
     path('', views.Welcome, name="home"),
    path('app/', AppView.as_view(),
          name='user_dashboard'),
    path('manual_expense/', ManualExpenseView.as_view(),
          name='manual_expense_form'),
  path('expense_list_view/', ExpenseListView.as_view(),
          name='expense_list'),
    path('receipt/', ReceiptProcessView.as_view(), 
         name='process_receipt'),     
]

#from this tutorial https://djangocentral.com/uploading-images-with-django/
if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)