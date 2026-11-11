from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.views import View
from .forms import AuthenticationForm


class Login(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'registration/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)  # Utilizza l'email come username
        if user is not None:
            login(request, user)
            messages.success(request, "Login effettuato con successo!")
            return redirect('struttura:macchina_homepage')
        else:
            messages.error(request, "Credenziali non valide.")
        return render(request, 'registration/login.html', {'form': form})


