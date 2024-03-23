from django.db import models
from django.contrib.auth.models import User
import datetime
from django.utils import timezone
	
# Create your models here.
class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	firstname = models.CharField(max_length=100, default='')
	lastname = models.CharField(max_length=100, default='')
	fathername = models.CharField(max_length=100)
	mothername = models.CharField(max_length=100)
	street = models.CharField(max_length=255)
	city = models.CharField(max_length=100)
	pincode = models.CharField(max_length=6)
	mobilenumber = models.CharField(max_length=10)
	def __str__(self):
		return self.user.username


class Branch(models.Model):
	branch_name = models.CharField(max_length=100)
	address = models.CharField(max_length=255)
	ifsc = models.CharField(max_length=11, unique=True)
	pincode = models.CharField(max_length=6)
	branch_id = models.CharField(max_length=2, choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(100)], default='00')

	def __str__(self):
		return self.branch_name



class Account(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	account_number = models.CharField(max_length=12, unique=True)
	ifsc = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
	balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	opened_date = models.DateField(default=timezone.now)
	is_active = models.BooleanField(default=True)
	account_holder_name = models.CharField(max_length=255, default='')

	def save(self, *args, **kwargs):
		if self.pk is None:
			if self.ifsc:
				branch_id = self.ifsc.branch_id
				account_numbers = Account.objects.filter(ifsc__branch_id=branch_id)
				next_account_number = str(account_numbers.count() + 1).zfill(6)
				self.account_number = f"2807{branch_id}{next_account_number}"

		profile = self.user.profile
		self.account_holder_name = f"{profile.firstname} {profile.lastname}"
		super().save(*args, **kwargs)

	def __str__(self):
		return self.account_number