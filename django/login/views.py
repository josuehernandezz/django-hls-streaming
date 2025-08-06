from django.shortcuts import render, redirect
from django.contrib import messages
from home.settings import PROJECT_NAME, PROJECT_YEAR

from .forms import SignIn
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash

# Create your views here.

redirect_app_url = 'home'

def signin_view(request):
    if request.method == "POST":
        form = SignIn(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if username and password:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    print(f"{user.username} logged in")
                    return redirect(redirect_app_url)
                else:
                    messages.error(request, "Wrong username or password.")
            else:
                # Add a general error message if username or password is empty
                messages.error(request, "Both username and password are required.")
    else:
        form = SignIn()
    context = {
        'form': form,
    }
    return render(request, 'login/signin.html', context)
