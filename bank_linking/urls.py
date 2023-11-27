from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import plaid_link_token, exchange_public_token


urlpatterns = [
    path('plaid-link-token/', plaid_link_token, name='plaid_link_token'),
    path('exchange-public-token/', exchange_public_token, name='exchange_public_token'),

         ]