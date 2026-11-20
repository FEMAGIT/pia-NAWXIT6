from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm
from .utils import authenticate_with_email

User = get_user_model()


class AuthenticationForm(BaseAuthenticationForm):
    email = forms.EmailField(
        max_length=150,
        label="E-mail",
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'E-mail',
                                      'tabindex': '1',
                                      'autofocus': 'autofocus',
                                      'required': 'required'
                                      })
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                          'placeholder': 'Password',
                                          'tabindex': '2'
                                          })
    )

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        user = authenticate_with_email(email=email, password=password)
        if user is None:
            raise forms.ValidationError("Credenziali non valide.")
        self.user_cache = user

        return self.cleaned_data

    def get_user(self):
        return self.user_cache



