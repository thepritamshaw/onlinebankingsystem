from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Profile, Branch, Account, Transaction
from decimal import Decimal

# Create your views here.
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

def logout(request):
	auth.logout(request)
	return redirect('/')

@login_required
def useraccounts(request):
	accounts = Account.objects.filter(user=request.user)
	branches = Branch.objects.all()
	return render(request, 'useraccounts.html', {'accounts': accounts, 'branches': branches})

@login_required
def createaccount(request):
	if request.method == 'POST':
		user = request.user
		branch_id = request.POST.get('branch')  # Get the selected branch ID from the form
		branch = Branch.objects.get(id=branch_id)
		account = Account.objects.create(
			user=user,
			branch_name=branch,
		)
		return redirect('useraccounts')  # Redirect to the user accounts page after account creation
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
			# Retrieve sender's account
			sender_account = Account.objects.get(id=sender_account_id)
		except Account.DoesNotExist:
			messages.error(request, 'Invalid sender account.')
			return redirect('initiate_transaction')

		# Validate sender's password
		if not sender_account.user.check_password(password):
			messages.error(request, 'Incorrect password.')
			return redirect('initiate_transaction')

		try:
			# Check if beneficiary account exists
			beneficiary_account = Account.objects.get(account_number=beneficiary_account_number, ifsc=beneficiary_ifsc)
		except Account.DoesNotExist:
			messages.error(request, 'Beneficiary account does not exist.')
			return redirect('initiate_transaction')

		if amount <= Decimal('0'):
			messages.error(request, 'Amount should be greater than ₹0')
			return redirect('initiate_transaction')

		beneficiary_name = beneficiary_account.account_holder_name
		sender_name = sender_account.account_holder_name

		# Check if sender has enough balance
		if sender_account.balance < amount:
			messages.error(request, 'Insufficient balance.')
			return redirect('initiate_transaction')

		# Perform transaction
		sender_account.balance -= amount
		sender_account.save()
		beneficiary_account.balance += amount
		beneficiary_account.save()

		# Create transaction record
		transaction = Transaction.objects.create(
			sender_account=sender_account,
			receiver_account_number=beneficiary_account_number,
			receiver_ifsc=beneficiary_ifsc,
			amount=amount,
			beneficiary_name=beneficiary_name,
			sender_name=sender_name,
		)
		return redirect('transaction_success', bank_reference_no=transaction.bank_reference_no)
	else:
		# Get the accounts of the logged-in user for the dropdown menu
		sender_accounts = Account.objects.filter(user=request.user)
		return render(request, 'initiate_transaction.html', {'sender_accounts': sender_accounts})
		
@login_required
def transaction_success(request, bank_reference_no=None):
	transaction = get_object_or_404(Transaction, bank_reference_no=bank_reference_no)
	sender_account_number = transaction.sender_account.account_number
	return render(request, 'transaction_success.html', {'transaction': transaction, 'sender_account_number': sender_account_number})


@login_required
def transaction_history(request):
    user = request.user
    accounts = Account.objects.filter(user=user)

    selected_account_number = request.GET.get('account_select')
    selected_account = accounts.filter(account_number=selected_account_number).first() if selected_account_number else None

    if selected_account:
        transactions = Transaction.objects.filter(sender_account=selected_account) | Transaction.objects.filter(receiver_account_number=selected_account.account_number)
    else:
        transactions = Transaction.objects.none()  # No transactions if no account selected

    # Prepare transaction data with dynamically calculated sender and receiver balances
    transaction_data = []
    for transaction in transactions:
        receiver_account = Account.objects.get(account_number=transaction.receiver_account_number)
        if transaction.sender_account.user == user:
            balance = transaction.sender_account.balance
        else:
            balance = receiver_account.balance
        transaction_data.append({'transaction': transaction, 'balance': balance})

    return render(request, 'transaction_history.html', {'transaction_data': transaction_data, 'selected_account': selected_account, 'accounts': accounts})


