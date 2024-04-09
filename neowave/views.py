from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Profile, Branch, Account, Transaction, Cheque
from decimal import Decimal
from num2words import num2words
from datetime import datetime
from django.db.models import Q

def index(request):
	return render(request, 'index.html')

def register(request):
	if request.method =='POST':
		firstname = request.POST['firstname']
		lastname = request.POST['lastname']
		fathername = request.POST['fathername']
		mothername = request.POST['mothername']
		street = request.POST['street']
		city = request.POST['city']
		pincode = request.POST['pincode']
		mobilenumber = request.POST['mobilenumber']
		username = request.POST['username']
		email = request.POST['email']
		password = request.POST['password']
		password1 = request.POST['password1']
		# nominee_name = request.POST['nominee_name']
		# relationship_with_nominee = request.POST['relationship_with_nominee']
		branch_id = request.POST.get('branch')
		branch = Branch.objects.get(id=branch_id)

		if password == password1:
			if User.objects.filter(email=email).exists():
				messages.info(request, 'Email already exists')
				return redirect('register')
			elif User.objects.filter(username=username).exists():
				messages.info(request, 'Username already exists')
				return redirect('register')
			else:
				user=User.objects.create_user(
					username=username,
					email=email,
					password=password
				)
				user.save()

				profile = Profile.objects.create(
					user=user,
					firstname=firstname,
					lastname=lastname,
					fathername=fathername,
					mothername=mothername,
					street=street,
					city=city,
					pincode=pincode,
					mobilenumber=mobilenumber,
					# nominee_name = nominee_name,
					# relationship_with_nominee=relationship_with_nominee,
				)

				account = Account.objects.create(
					user=user,
					branch_name=branch,
				)

				return redirect('login')
		else:
			messages.info(request, 'Password not Matching')
			return redirect('register')
	else:
		branches = Branch.objects.all()
		return render(request, 'register.html', {'branches': branches})

def login(request):
	if request.method =='POST':
		username = request.POST['username']
		password = request.POST['password']

		user= auth.authenticate(username=username, password=password)
		if user is not None:
			auth.login(request, user)
			return redirect ('/')
		else:
			messages.info(request, 'Credentials Invalid')
			return redirect ('login')
	return render(request, 'login.html')

@login_required
def logout(request):
	auth.logout(request)
	return redirect('/')

@login_required
def useraccounts(request):
	accounts = Account.objects.filter(user=request.user)
	branches = Branch.objects.all()
	return render(request, 'useraccounts.html', {'accounts': accounts, 'branches': branches})

@login_required
def change_branch(request):
	if request.method == 'POST':
		account_number = request.POST.get('account_number')
		branch_id = request.POST.get('branch')
		try:
			account = Account.objects.get(account_number=account_number)
			branch = Branch.objects.get(id=branch_id)
			account.branch_name = branch
			account.ifsc = branch.ifsc
			account.save()
			return redirect('useraccounts')
		except (Account.DoesNotExist, Branch.DoesNotExist):
			# Handle errors here (e.g., display an error message)
			pass
	# Redirect to useraccounts page if the request method is not POST or if there's an error
	return redirect('useraccounts')

@login_required
def createaccount(request):
	if request.method == 'POST':
		user = request.user
		branch_id = request.POST.get('branch')
		branch = Branch.objects.get(id=branch_id)
		account = Account.objects.create(
			user=user,
			branch_name=branch,
		)
		return redirect('useraccounts')
	else:
		branches = Branch.objects.all()
		return render(request, 'createaccount.html', {'branches': branches})

def get_beneficiary_name(request):
	if request.method == 'GET':
		account_number = request.GET.get('account_number')
		ifsc = request.GET.get('ifsc')

		try:
			beneficiary_account = Account.objects.get(account_number=account_number, ifsc=ifsc)
			beneficiary_name = beneficiary_account.account_holder_name
			return JsonResponse({'beneficiary_name': beneficiary_name})
		except Account.DoesNotExist:
			return JsonResponse({'error': 'Beneficiary account not found'}, status=404)

@login_required
def initiate_transaction(request):
	if request.method == 'POST':
		sender_account_id = request.POST.get('sender_account')
		beneficiary_account_number = request.POST.get('beneficiary_account_number')
		beneficiary_ifsc = request.POST.get('beneficiary_ifsc')
		amount = Decimal(request.POST.get('amount'))
		password = request.POST.get('password')

		try:
			sender_account = Account.objects.get(id=sender_account_id)
		except Account.DoesNotExist:
			messages.error(request, 'Invalid sender account.')
			return redirect('initiate_transaction')

		if not sender_account.user.check_password(password):
			messages.error(request, 'Incorrect password.')
			return redirect('initiate_transaction')

		try:
			beneficiary_account = Account.objects.get(account_number=beneficiary_account_number, ifsc=beneficiary_ifsc)
		except Account.DoesNotExist:
			messages.error(request, 'Beneficiary account does not exist.')
			return redirect('initiate_transaction')

		try:
			transaction = Transaction(
				sender_account=sender_account,
				receiver_account_number=beneficiary_account_number,
				receiver_ifsc=beneficiary_ifsc,
				amount=amount,
				beneficiary_name=beneficiary_account.account_holder_name,
				sender_name=sender_account.account_holder_name
			)
			transaction.save()
			
			return redirect('transaction_success', bank_reference_no=transaction.bank_reference_no)
		except ValueError as e:
			messages.error(request, str(e))
			return redirect('initiate_transaction')

	else:
		sender_accounts = Account.objects.filter(user=request.user)
		return render(request, 'initiate_transaction.html', {'sender_accounts': sender_accounts})

@login_required
def transaction_success(request, bank_reference_no=None):
	transaction = get_object_or_404(Transaction, bank_reference_no=bank_reference_no)

	if request.user != transaction.sender_account.user:
		return HttpResponseForbidden("You are not authorized to view this page.")

	sender_account_number = transaction.sender_account.account_number

	amount_in_words = num2words(transaction.amount, lang='en_IN').capitalize()
	
	context = {
		'transaction': transaction,
		'sender_account_number': sender_account_number,
		'amount_in_words': amount_in_words,
	}
	return render(request, 'transaction_success.html', context)

@login_required
def transaction_history(request):
	user = request.user
	accounts = Account.objects.filter(user=user)

	selected_account_number = request.GET.get('account_select')
	selected_account = accounts.filter(account_number=selected_account_number).first()

	if selected_account:
		transactions_sent = Transaction.objects.filter(sender_account=selected_account)
		transactions_received = Transaction.objects.filter(receiver_account_number=selected_account.account_number)
		transactions = transactions_sent | transactions_received
	else:
		transactions = Transaction.objects.none()

	transaction_data = []

	for transaction in transactions:
		if transaction.sender_account == selected_account:
			balance = transaction.sender_balance_after_transaction
		else:
			balance = transaction.receiver_balance_after_transaction
		
		transaction_data.append({'transaction': transaction, 'balance': balance})

	return render(request, 'transaction_history.html', {'transaction_data': transaction_data, 'selected_account': selected_account, 'accounts': accounts})

@login_required
def userdetails(request):
	profile = request.user.profile

	if request.method == 'POST':
		profile.firstname = request.POST['firstname']
		profile.lastname = request.POST['lastname']
		profile.fathername = request.POST['fathername']
		profile.mothername = request.POST['mothername']
		profile.street = request.POST['street']
		profile.city = request.POST['city']
		profile.pincode = request.POST['pincode']
		profile.mobilenumber = request.POST['mobilenumber']
		profile.save()

		return redirect('index')

	return render(request, 'userdetails.html', {'profile': profile})

@login_required
def cheque_details(request):
	user = request.user
	accounts = Account.objects.filter(user=user)

	selected_account_number = request.GET.get('account_select')
	selected_account = accounts.filter(account_number=selected_account_number).first()
	cheques = []

	if selected_account:
		cheques = Cheque.objects.filter(user_account=selected_account)

	return render(request, 'cheque.html', {'cheques': cheques, 'accounts': accounts, 'selected_account': selected_account, 'stop_reason_choices': Cheque.STOP_REASON_CHOICES})

@login_required
def stop_cheque(request):
	if request.method == 'POST':
		cheque_number = request.POST.get('cheque_number')
		stop_reason = request.POST.get('stop_reason')

		try:
			cheque = Cheque.objects.get(cheque_number=cheque_number)
			if cheque.status == 'pending':
				cheque.stop_payment(request.user, stop_reason)
				return JsonResponse({'success': True, 'message': 'Cheque stopped successfully.'})
			else:
				return JsonResponse({'success': False, 'message': 'Cheque is not in pending status, cannot be stopped.'})
		except Cheque.DoesNotExist:
			return JsonResponse({'success': True, 'message': 'Cheque stopped successfully.'})

	return JsonResponse({'success': False, 'message': 'Invalid request.'})

@login_required
def get_statement(request):
	if request.method == 'POST':
		month = request.POST.get('month')
		year = request.POST.get('year')
		user = request.user

		accounts = Account.objects.filter(user=user)
		transaction_data = {}
		
		for account in accounts:
			transactions_sent = Transaction.objects.filter(sender_account=account)
			transactions_received = Transaction.objects.filter(receiver_account_number=account.account_number)
			transactions = transactions_sent | transactions_received
			if month:
				transactions = transactions.filter(timestamp__month=month)
			if year:
				transactions = transactions.filter(timestamp__year=year)

			transaction_data[account.account_number] = transactions

		return render(request, 'transaction_statement.html', {'transaction_data': transaction_data})
	
	return render(request, 'get_statement.html')

@login_required
def transaction_statement(request):
	user = request.user
	accounts = Account.objects.filter(user=user)
	transaction_data = {}

	month = request.POST.get('month')
	year = int(request.POST.get('year'))

	for account in accounts:
		if month:
			opening_balance, closing_balance = get_opening_closing_balance(account, int(month), year)
		else:
			# If month is not selected, get the statement for the entire year
			opening_balance, closing_balance = get_opening_closing_balance(account, None, year)

		transactions_sent = Transaction.objects.filter(sender_account=account)
		transactions_received = Transaction.objects.filter(receiver_account_number=account.account_number)
		transactions = transactions_sent | transactions_received

		if month:
			transactions = transactions.filter(timestamp__month=int(month))
		transactions = transactions.filter(timestamp__year=year)

		transaction_data[account.account_number] = {
			'transactions': transactions,
			'opening_balance': opening_balance,
			'closing_balance': closing_balance,
			'ifsc': account.ifsc
		}

	return render(request, 'transaction_statement.html', {'transaction_data': transaction_data})

def get_opening_closing_balance(account, month, year):

	if month is None:
		first_day_of_month = datetime(year, 1, 1)
	else:
		first_day_of_month = datetime(year, month, 1)

	# Get the last transaction before the target month
	last_transaction_before_month = Transaction.objects.filter(
		Q(sender_account=account) | Q(receiver_account_number=account.account_number),
		timestamp__lt=first_day_of_month
	).order_by('-timestamp').first()

	# Get the first transaction after the target month
	first_transaction_after_month = Transaction.objects.filter(
		Q(sender_account=account) | Q(receiver_account_number=account.account_number),
		timestamp__gte=first_day_of_month
	).order_by('timestamp').first()

	if month is not None:
		next_month = month + 1
		next_year = year

		if next_month > 12:
			next_month = 1
			next_year += 1
		first_day_of_next_month = datetime(next_year, next_month, 1)
	else:
		next_year = year+1
		first_day_of_next_month = datetime(next_year, 1, 1)

	opening_balance = account.balance

	# Use the current account balance if no transactions before the target month
	if last_transaction_before_month is None:
		if first_transaction_after_month is None:
			return opening_balance, opening_balance  # No transactions at all
		if first_transaction_after_month.sender_account == account:
			opening_balance = first_transaction_after_month.sender_balance_after_transaction + first_transaction_after_month.amount
		else:
			opening_balance = first_transaction_after_month.receiver_balance_after_transaction - first_transaction_after_month.amount
	elif first_transaction_after_month is None:
		if last_transaction_before_month.sender_account == account:
			opening_balance = last_transaction_before_month.sender_balance_after_transaction
		else:
			opening_balance = last_transaction_before_month.receiver_balance_after_transaction
		return opening_balance, opening_balance  # No transactions after the target month
	else:
		if first_transaction_after_month.sender_account == account:
			opening_balance = first_transaction_after_month.sender_balance_after_transaction + first_transaction_after_month.amount
		else:
			opening_balance = first_transaction_after_month.receiver_balance_after_transaction - first_transaction_after_month.amount

	# Calculate the closing balance for the target month
	transactions_in_month = Transaction.objects.filter(
		Q(sender_account=account) | Q(receiver_account_number=account.account_number),
		timestamp__gte=first_day_of_month,
		timestamp__lt=first_day_of_next_month
	)

	closing_balance = opening_balance
	for transaction in transactions_in_month:
		if transaction.sender_account == account:
			closing_balance -= transaction.amount
		else:
			closing_balance += transaction.amount

	return opening_balance, closing_balance
