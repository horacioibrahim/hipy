from django.shortcuts import render



def home(request):
	return render(request, 'feedback360/home.html')

def test_fb(request):
	return render(request, 'feedback360/test_fb.html')

def access(request):
	username = None
	
	if request.method == "POST":
		username = request.POST['username']
		status = request.POST['status']

		if status == 'connected':
			return render(request, 'ok')

	return render(request, 'feedback360/test_fb.html', dict(u=username))	
