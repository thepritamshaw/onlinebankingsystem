from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
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
	# nominee_name = models.CharField(max_length=100)
	# relationship_with_nominee = models.CharField(max_length=100)
	def __str__(self):
		return self.user.username

class Branch(models.Model):
	branch_name = models.CharField(max_length=100)
	address = models.CharField(max_length=255)
	ifsc = models.CharField(max_length=11, unique=True)
	pincode = models.CharField(max_length=6)
	def __str__(self):
		return self.branch_name

class Account(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	account_number = models.CharField(max_length=12, unique=True)
	branch_name = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
	ifsc = models.CharField(max_length=11, default='')
	balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	opened_date = models.DateField(default=datetime.now)
	is_active = models.BooleanField(default=True)
	account_holder_name = models.CharField(max_length=255, default='')

	def save(self, *args, **kwargs):
		if self.pk is None:
			if self.branch_name:
				self.ifsc = self.branch_name.ifsc

				account_numbers = Account.objects.filter(branch_name=self.branch_name)
				next_account_number = str(account_numbers.count() + 1).zfill(6)
				self.account_number = f"{self.branch_name.ifsc[-6:]}{next_account_number}"

		profile = self.user.profile
		self.account_holder_name = f"{profile.firstname} {profile.lastname}"
		super().save(*args, **kwargs)

	def __str__(self):
		return self.account_number


class Transaction(models.Model):
	sender_account = models.ForeignKey(Account, related_name='sent_transactions', on_delete=models.CASCADE)
	receiver_account_number = models.CharField(max_length=12)
	receiver_ifsc = models.CharField(max_length=11)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	sender_name = models.CharField(max_length=255, default='')
	beneficiary_name = models.CharField(max_length=255, default='')
	bank_reference_no = models.CharField(max_length=10, unique=True, blank=True, null=True)
	sender_balance_after_transaction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	receiver_balance_after_transaction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	timestamp = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		if not self.bank_reference_no:
			last_transaction = Transaction.objects.filter(bank_reference_no__isnull=False).order_by('-bank_reference_no').first()
			if last_transaction:
				last_reference_no = int(last_transaction.bank_reference_no[1:])
				new_reference_no = last_reference_no + 1
				self.bank_reference_no = f'B{str(new_reference_no).zfill(8)}'
			else:
				self.bank_reference_no = 'B00000001'

		super().save(*args, **kwargs)

	def __str__(self):
		return self.bank_reference_no