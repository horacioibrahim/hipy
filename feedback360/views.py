from django.shortcuts import render



def home(request):
	return render(request, 'feedback360/home.html')

def test_fb(request):
	return render(request, 'feedback360/test_fb.html')

def access(request):

	name = None
	email = None	

	if request.method == "POST":
		name = request.POST.get('name', None)
		email = request.POST.get('email', None)

		if check_sent(email):
			pass # If true -> Thanks
		else:
			pass # redirect questions or return JSON, etc.

	# not return here is need
	return render(request, 'feedback360/test_fb.html', dict(u=username))	

def check_sent(email):
	pass