from django.contrib import admin
from .models import Profile, Branch, Account

admin.site.register(Profile)
admin.site.register(Branch)

class AccountAdmin(admin.ModelAdmin):
	list_display = ('account_number', 'user', 'ifsc', 'account_holder_name', 'balance', 'opened_date', 'is_active')
	readonly_fields = ('account_holder_name', 'account_number', 'opened_date',)

	def save_model(self, request, obj, form, change):
		obj.account_holder_name = f"{obj.user.profile.user.first_name} {obj.user.profile.user.last_name}"

		if obj.pk is None:
			branch_id = obj.ifsc.branch_id
			account_numbers = Account.objects.filter(ifsc__branch_id=branch_id)
			next_account_number = str(account_numbers.count() + 1).zfill(6)
			obj.account_number = f"2807{branch_id}{next_account_number}"

		super().save_model(request, obj, form, change)

admin.site.register(Account, AccountAdmin)
