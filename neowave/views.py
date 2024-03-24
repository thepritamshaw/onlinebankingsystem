from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Profile, Branch, Account
from django.utils import timezone

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