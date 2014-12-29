from django.shortcuts import render



def home(request):
	return render(request, 'feedback360/home.html')


