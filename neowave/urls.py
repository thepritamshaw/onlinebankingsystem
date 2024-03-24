from django.urls import path
from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path('register', views.register, name='register'),
	path('login', views.login, name= 'login'),
	path('logout', views.logout, name= 'logout'),
	path('useraccounts', views.useraccounts, name= 'useraccounts'),
	path('createaccount', views.createaccount, name='createaccount'),
	path('initiate_transaction', views.initiate_transaction, name='initiate_transaction'),
	path('transaction_success', views.transaction_success, name='transaction_success'),
]