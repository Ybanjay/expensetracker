from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import get_transactions, plaid_link_token, exchange_public_token


#https://dashboard.plaid.com/developers/sandbox.
urlpatterns = [
    path('plaid-link-token/', plaid_link_token, name='plaid_link_token'),
    path('exchange-public-token/', exchange_public_token, name='exchange_public_token'),
    path('get_transactions/',  get_transactions, name="get_transactions"),
         ]

#https://docs.djangoproject.com/en/4.2/intro/tutorial01/.