from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Profile

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
					fathername=fathername,
					mothername=mothername,
					street=street,
					city=city,
					pincode=pincode,
					mobilenumber=mobilenumber
				)
				return redirect('login')
		else:
			messages.info(request, 'Password not Matching')
			return redirect('register')
	else:
		return render(request, 'register.html')

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
