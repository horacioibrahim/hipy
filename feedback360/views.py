from django.shortcuts import render



def home(request):
	return render(request, 'feedback360/home.html')

def test_fb(request):
	return render(request, 'feedback360/test_fb.html')
