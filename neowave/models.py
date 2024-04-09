from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

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
				# Get the last 6 digits of the branch IFSC
				branch_ifsc_suffix = self.branch_name.ifsc[-6:]
				# Filter accounts with the same branch IFSC suffix
				accounts_with_suffix = Account.objects.filter(account_number__startswith=branch_ifsc_suffix)
				# Get the last account with the same branch IFSC suffix
				last_account_with_suffix = accounts_with_suffix.order_by('-account_number').first()
				
				if last_account_with_suffix:
					# Extract the numeric part of the account number
					last_account_number = int(last_account_with_suffix.account_number[-6:])
					# Generate the new account number by incrementing the last one
					new_account_number = str(last_account_number + 1).zfill(6)
					self.account_number = f"{branch_ifsc_suffix}{new_account_number}"
				else:
					# If no account exists for this branch, start with '000001'
					self.account_number = f"{branch_ifsc_suffix}000001"
				self.ifsc = self.branch_name.ifsc

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

		if self.sender_account.balance < self.amount:
			raise ValueError('Insufficient balance.')
		
		self.sender_account.balance -= self.amount
		self.sender_balance_after_transaction = self.sender_account.balance

		try:
			receiver_account = Account.objects.get(account_number=self.receiver_account_number, ifsc=self.receiver_ifsc)
		except Account.DoesNotExist:
			raise ValueError('Receiver account does not exist.')

		receiver_account.balance += self.amount
		self.receiver_balance_after_transaction = receiver_account.balance

		self.sender_account.save()
		receiver_account.save()

		super().save(*args, **kwargs)

	def __str__(self):
		return self.bank_reference_no

class Cheque(models.Model):
	CHEQUE_STATUS_CHOICES = [
		('pending', 'Pending'),
		('cleared', 'Cleared'),
		('stopped', 'Stopped'),
	]
	STOP_REASON_CHOICES = [
		('lost', 'Cheque Reported Lost'),
		('stopped', 'Payment Stopped by Drawer'),
	]
	user_account = models.ForeignKey(Account, on_delete=models.CASCADE)
	cheque_number = models.CharField(max_length=20, unique=True)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	recipient = models.CharField(max_length=100)
	status = models.CharField(max_length=10, choices=CHEQUE_STATUS_CHOICES, default='pending')
	stop_reason = models.CharField(max_length=10, choices=STOP_REASON_CHOICES, blank=True, null=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cheques_created')
	stopped_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cheques_stopped')
	created_at = models.DateTimeField(auto_now_add=True)

	def stop_payment(self, user, stop_reason):
		if self.status == 'pending':
			self.status = 'stopped'
			self.stopped_by = user
			self.stop_reason = stop_reason
			self.save()
			
	@property
	def issuer(self):
		return self.user_account.account_holder_name

	def __str__(self):
		return self.cheque_number
