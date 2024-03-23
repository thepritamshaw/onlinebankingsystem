from django.db import models
from django.contrib.auth.models import User
	
# Create your models here.
class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	fathername = models.CharField(max_length=100)
	mothername = models.CharField(max_length=100)
	street = models.CharField(max_length=255)
	city = models.CharField(max_length=100)
	pincode = models.CharField(max_length=6)
	mobilenumber = models.CharField(max_length=10)
