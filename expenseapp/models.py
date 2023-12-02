
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Expense(models.Model):
     user = models.ForeignKey(User, on_delete=models.CASCADE)
     store_name = models.CharField(max_length=35)
     amount = models.DecimalField(max_digits=20, decimal_places=3)
     date = models.DateField()
     category = models.CharField(max_length=35)
     receipt_image_path = models.CharField(max_length=277, blank=True, null=True)


#this is the model for storing 
#plaid access_token and item_id
class Bank_Token(models.Model):
      user = models.ForeignKey(User, on_delete=models.CASCADE)
      access_token = models.CharField(max_length=255)
      item_id = models.CharField(max_length=255)