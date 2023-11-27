from django.shortcuts import render,redirect
from django.http import JsonResponse
from plaid.api import plaid_api
import plaid
import datetime
import os
import json
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from django.views.decorators.csrf import csrf_exempt
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_account_filters import LinkTokenAccountFilters
from plaid.model.depository_filter import DepositoryFilter
from plaid.model.depository_account_subtypes import DepositoryAccountSubtypes
from plaid.model.depository_account_subtype import DepositoryAccountSubtype
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from django.contrib.auth.decorators import login_required
from expenseapp.models import Expense
from django.contrib import messages
#from expenseapp.models import Bank_Token

# Create your views here.
# plaid client config
def plaid_config():

    client_id = "6564ee36524852001cc0c409"

    secret = "7c86d9ea5d2689bed8acdc36c94927"
    
    configuration = plaid.Configuration(
                    host=plaid.Environment.Sandbox,
                    api_key={
                    'clientId': client_id,
                    'secret': secret,
                    }
                )

    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    
    return client

@csrf_exempt
@login_required
def plaid_link_token(request):
    PLAID_REDIRECT_URI = 'https://ybanjay.pythonanywhere.com'  
    
    client = plaid_config()

    requesting = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(
            client_user_id=str(request.user.id),
        ),
        client_name='My Expense App',
        products=[Products('transactions')],
        country_codes=[CountryCode('GB')],
        language='en',
        required_if_supported_products=[Products('liabilities')],
        webhook='https://sample-web-hook.com',
        redirect_uri=PLAID_REDIRECT_URI,
        account_filters=LinkTokenAccountFilters(
            depository=DepositoryFilter(
                account_subtypes=DepositoryAccountSubtypes([
                    DepositoryAccountSubtype('checking'),
                    DepositoryAccountSubtype('savings')
                ])
            )
        )
    )

    if PLAID_REDIRECT_URI is not None:
        request.redirect_uri = PLAID_REDIRECT_URI

    # Create link token
    response = client.link_token_create(requesting)

    link_token = response['link_token']

    return render(request, 'link_account.html', {'link_token': link_token})

@csrf_exempt
@login_required
def exchange_public_token(request):
    global access_token, item_id
    client = plaid_config()
    
    request_data = json.loads(request.body)
    public_token = request_data.get('public_token', '')
    #public_token= "public-sandbox-413e5a85-4f50-4200-b288-d6d9bf79c667"
    
    requesting = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    
    response = client.item_public_token_exchange(requesting)
    
    # These values should be saved to a persistent database and
    # associated with the currently signed-in user
    access_token = response['access_token']
    item_id = response['item_id']

    return JsonResponse({"access Token": access_token})

    #bank_token = Bank_Token(user=request.user, access_token=access_token, item_id=item_id)
    
    #return JsonResponse({'linkinkg_status': "Your Account Has Been Linked Successfully"})

