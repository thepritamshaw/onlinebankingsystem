from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Branch, Account, Transaction, Cheque

@receiver(post_save, sender=Profile)
def update_account_holder_name(sender, instance, created, **kwargs):
	if created or instance.firstname != instance.user.first_name or instance.lastname != instance.user.last_name:
		instance.user.first_name = instance.firstname
		instance.user.last_name = instance.lastname
		instance.user.save()

		accounts = instance.user.account_set.all()
		for account in accounts:
			account.account_holder_name = f"{instance.firstname} {instance.lastname}"
			account.save()

		transactions1 = Transaction.objects.filter(sender_account__user=instance.user)
		transactions1.update(sender_name=instance.user.get_full_name())

		receiver_account_numbers = accounts.values_list('account_number', flat=True)
		transactions2 = Transaction.objects.filter(receiver_account_number__in=receiver_account_numbers)
		transactions2.update(beneficiary_name=instance.user.get_full_name())

@receiver(pre_save, sender=Account)
def update_ifsc_in_transactions(sender, instance, **kwargs):
	if instance.pk:
		try:
			original_instance = Account.objects.get(pk=instance.pk)
			if original_instance.branch_name != instance.branch_name:
				transactions = Transaction.objects.filter(receiver_account_number=instance.account_number)
				transactions.update(receiver_ifsc=instance.branch_name.ifsc)
		except Account.DoesNotExist:
			pass

@receiver(pre_save, sender=Branch)
def update_related_models(sender, instance, **kwargs):
	accounts = Account.objects.filter(branch_name=instance)
	accounts.update(ifsc=instance.ifsc)

	for account in accounts:
		if account.branch_name != instance.branch_name:
			transactions = Transaction.objects.filter(receiver_account_number=account.account_number)
			transactions.update(receiver_ifsc=instance.ifsc)
