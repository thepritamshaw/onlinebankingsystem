from django.urls import path
from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path('register', views.register, name='register'),
	path('login', views.login, name= 'login'),
	path('logout', views.logout, name= 'logout'),
	path('useraccounts', views.useraccounts, name= 'useraccounts'),
    path('change_branch/', views.change_branch, name='change_branch'),
	path('createaccount', views.createaccount, name='createaccount'),
	path('initiate_transaction', views.initiate_transaction, name='initiate_transaction'),
	path('transaction_success/<str:bank_reference_no>/', views.transaction_success, name='transaction_success'),
	path('get_beneficiary_name/', views.get_beneficiary_name, name='get_beneficiary_name'),
	path('transaction_history', views.transaction_history, name= 'transaction_history'),
	path('userdetails', views.userdetails, name= 'userdetails'),
	path('cheque_details', views.cheque_details, name='cheque_details'),
	path('stop_cheque/', views.stop_cheque, name='stop_cheque'),
	path('get_statement/', views.get_statement, name='get_statement'),
	path('transaction_statement/', views.transaction_statement, name='transaction_statement'),
]