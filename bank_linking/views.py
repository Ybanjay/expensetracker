from django.shortcuts import render,redirect
from django.http import JsonResponse
from plaid.api import plaid_api
import plaid
import datetime
from dotenv import load_dotenv
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
from expenseapp.models import Bank_Token, Expense
from django.contrib import messages
#from expenseapp.models import Bank_Token

# Create your views here.

#https://dashboard.plaid.com/developers/sandbox.
# plaid client config
def plaid_config():
    load_dotenv()
    client_id = os.getenv('PLAID_CLIENT_ID')

    secret = os.getenv('PLAID_SECRET')
    
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
    
    requesting = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    
    response = client.item_public_token_exchange(requesting)
    
    # These values should be saved to a persistent database and
    # associated with the currently signed-in user
    access_token = response['access_token']
    item_id = response['item_id']
    
    #save access token and item id in the database for 
    # for subsequent usage
    bank_token = Bank_Token(user=request.user, access_token=access_token, item_id=item_id)
    
    bank_token.save()
    return JsonResponse({'linkinkg_status': "Your Account Has Been Linked Successfully"})

#This get transaction function is based 
#on the official plaid quickstart for integration
# with python(https://plaid.com/docs/quickstart/)
def get_transactions(request):
    #global access_token
    client = plaid_config()
   # Set cursor to empty to receive all historical updates
    cursor = ''
       # New transaction updates since "cursor"
    my_access_token = Bank_Token.objects.filter(user=request.user)
    for my_access in my_access_token:

        access_token = my_access.access_token
    added = []
    modified = []
    removed = [] 
    has_more = True
    batch_size = 5
    try:
        # Iterate through each page of new transaction updates for item
        while has_more:
            requesting = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
                count=batch_size 

            )
            response = client.transactions_sync(requesting).to_dict()
            # Add this page of results
            added.extend(response['added'])
            modified.extend(response['modified'])
            removed.extend(response['removed'])
            has_more = response['has_more']
            # Update cursor to the next cursor
            cursor = response['next_cursor']
            #pretty_print_response(response)

        """
    except plaid.ApiException as e:

        error_response = e

        messages.error(request, error_response) 
     """
        # Return the 5 most recent transactions
        
        latest_transactions = sorted(added, key=lambda t: t['date'])[-5:]
      
        for transaction in latest_transactions:
            # expense transactions only.
            #According to the plaid docs positive amounts 
            #indicates outgoing transactions from the account which depicts expenses
            if transaction.get('amount') > 0:
                transaction_name = transaction.get('name')
                transaction_amount = transaction.get('amount')
                transaction_category = transaction.get('category')[0]
                transaction_date = transaction.get('date')

                exepnse_transactions = Expense(user=request.user, store_name=transaction_name, amount = transaction_amount, \
                                               date = transaction_date, category = transaction_category)

                exepnse_transactions.save()

        messages.success(request, 'Expense Transactions  successfully Added!')

        return redirect("expense_list")
    
        
    except plaid.ApiException as e:

        error_response = e

        messages.error(request, error_response)  

        return redirect("plaid_link_token")
    
def pretty_print_response(response):
  print(json.dumps(response, indent=2, sort_keys=True, default=str))