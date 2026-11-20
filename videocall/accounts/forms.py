from django import forms
from django.forms import ModelChoiceField
from .models import SmartGlass,User
from material import Layout, Row
from django.db.models import Q



class CustomModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name






class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label='Vecchia Password', max_length=50,
                                    widget=forms.PasswordInput(), required=True)

    password = forms.CharField(label='Nuova Password', max_length=50,
                               widget=forms.PasswordInput(), required=True)
    confirm_password = forms.CharField(label='Conferma la Password', max_length=50,
                               widget=forms.PasswordInput(), required=True)

    layout = Layout('password', 'confirm_password')

    def __init__(self,user, data=None, files=None, recipient_list=None, *args, **kwargs):
        super().__init__(data=data, files=files, *args, **kwargs)
        self.user=user
    class Meta:
        model = User
        fields = ('password', 'confirm_password',)

    def clean(self):
        form_data = self.cleaned_data
        password = self.cleaned_data.get('password', None)
        confirm_password = self.cleaned_data.get('confirm_password', None)
        old_password = self.cleaned_data.get('old_password', None)
        if password != confirm_password:
            self.add_error("password","La Password non Corrisponde")  # Will raise a error message
            del form_data['password']
            del form_data['confirm_password']

        if not old_password or not self.user.check_password(old_password)  :
            self.add_error("old_password", "Password old_password")  # Will raise a error message
            del form_data['old_password']


class LoginForm(forms.Form):

    username = forms.CharField(label='Username', max_length=50,
                               widget=forms.TextInput())
    password = forms.CharField(label='Password', max_length=50,
                               widget=forms.PasswordInput())
    layout = Layout('username', 'password')

    def __init__(self, data=None, files=None, recipient_list=None, *args, **kwargs):
        super().__init__(data=data, files=files, *args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'input100'
        self.fields['password'].widget.attrs['class'] = 'input100'

    class Meta:
        model = User
        fields = ('username', 'password')




class MyPasswordWidget(forms.PasswordInput):
    template_name = 'accounts/my_password_widget.html'



class AddNewUserForm(forms.ModelForm):
    username = forms.CharField(label='Username', max_length=50,
                               widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    first_name = forms.CharField(label='Nome', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Nome'}))
    last_name = forms.CharField(label='Cognome', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Cognome'}))
    password = forms.CharField(label='Password', max_length=50,
                               widget=MyPasswordWidget,required=True)
    email = forms.CharField(label='Email', max_length=50,
                            widget=forms.EmailInput(attrs={'placeholder': 'Email'}))

    layout = Layout(Row('first_name', 'last_name'),
                    'username', 'email',
                    Row('password', 'confirm_password'))

    your_password = forms.CharField(label='La Tua Password', max_length=50,
                               widget=MyPasswordWidget, required=True)

    def __init__(self, user, data=None, files=None, recipient_list=None, *args, **kwargs):
        self.user = user
        super().__init__(data=data, files=files, *args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        if not user.is_superuser:
            self.fields['is_superuser'].widget = forms.HiddenInput()


    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password', 'email', 'is_superuser')

    def clean_your_password(self):
        form_data = super(AddNewUserForm, self).clean()
        your_password=self.cleaned_data.get('your_password', None)
        if not your_password or not self.user.check_password(your_password):
            self.add_error("your_password","Password Errata")
        return form_data


class CreateSmartGlass(forms.ModelForm):
    name = forms.CharField(label='Etichetta SmartGlass', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Etichetta dello SmartGlass'}))
    serial = forms.CharField(label='Seriale SmartGlass', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Seriale dello SmartGlass'}))
    modify = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=True)

    def __init__(self, data=None, files=None,disabled=False, ata=None, recipient_list=None, *args, **kwargs):
        super().__init__(data=data, files=files, *args, **kwargs)
        self.fields['serial'].widget.attrs['class'] = 'form-control'
        self.fields['name'].widget.attrs['class'] = 'form-control'
        if not disabled and ata:
            self.fields['serial'].initial = ata.serial

        self.fields['serial'].disabled = disabled
        self.fields['name'].disabled = disabled
        self.fields['modify'].initial = disabled

    class Meta:
        model = SmartGlass
        fields = ( 'name', 'serial')


class CreateZone(forms.ModelForm):
    name = forms.CharField(label='Nome Zona', max_length=50,
                           widget=forms.TextInput(attrs={'placeholder': 'Nome Zona'}))
    ssid = forms.CharField(label='SSID WIFI', max_length=50,
                             widget=forms.TextInput(attrs={'placeholder': 'SSID WIFI'}))
    password = forms.CharField(label='Password WIFI', max_length=50,
                             widget=forms.TextInput(attrs={'placeholder': 'Password WIFI'}))
    modify = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=True)

    def __init__(self, data=None, files=None,disabled=False, recipient_list=None, *args, **kwargs):
        super().__init__(data=data, files=files, *args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['ssid'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['protocol'].widget.attrs['class'] = 'form-control'

        self.fields['name'].disabled = disabled
        self.fields['ssid'].disabled = disabled
        self.fields['password'].disabled = disabled
        self.fields['protocol'].disabled = disabled
        self.fields['modify'].initial = disabled

    class Meta:
      #  model = Zone
        fields = ('name', 'ssid', 'password', 'protocol')



class ModifyUserForm(forms.ModelForm):
    username = forms.CharField(label='Username', max_length=50,
                               widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    first_name = forms.CharField(label='Nome', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Nome'}))
    last_name = forms.CharField(label='Cognome', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Cognome'}))
    password = forms.CharField(label='Password', max_length=50,
                               widget=MyPasswordWidget, required=False)
    email = forms.CharField(label='Email', max_length=50,
                            widget=forms.EmailInput(attrs={'placeholder': 'Email'}))

    modify = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=True)

    layout = Layout(Row('first_name', 'last_name'),
                    'username', 'email',
                    Row('password', 'confirm_password'))
    is_superuser = forms.BooleanField(widget=forms.CheckboxInput(), required=False, initial=False)

    your_password = forms.CharField(label='La Tua Password', max_length=50,
                                    widget=MyPasswordWidget, required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password', 'email', 'is_superuser')

    def __init__(self, user, user_to_modify, disabled=True, data=None, files=None, recipient_list=None, *args, **kwargs):
        self.user = user
        self.user_to_modify=user_to_modify
        super().__init__(data=data, files=files, *args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'


        self.fields['first_name'].disabled = disabled
        self.fields['username'].disabled = disabled

        self.fields['password'].disabled = disabled
        self.fields['your_password'].disabled = disabled

        self.fields['is_superuser'].disabled = disabled

        if not self.user.is_superuser:
            self.fields['is_superuser'].widget = forms.HiddenInput()

        if disabled:
            self.fields['password'].widget = forms.HiddenInput()
            self.fields['your_password'].widget = forms.HiddenInput()

        self.fields['last_name'].disabled = disabled
        self.fields['email'].disabled = disabled
        self.fields['modify'].initial = disabled

        self.fields['first_name'].initial = user_to_modify.first_name
        self.fields['username'].initial = user_to_modify.username
        self.fields['password'].initial = ''
        self.fields['last_name'].initial = user_to_modify.last_name
        self.fields['email'].initial= user_to_modify.email
        self.fields['is_superuser'].initial = user_to_modify.is_superuser

    def clean(self):
        form_data = self.cleaned_data

        tempqueryset=User.objects.filter(Q(username = form_data['username']), ~Q(pk=self.user_to_modify.pk ))
        if tempqueryset.exists():
            self.add_error("username","username già in uso")

        if not self.user.is_superuser:
            if form_data['is_superuser'] != self.user_to_modify.is_superuser :
                    self.add_error("is_superuser","non puoi modificare questo campo")

        if not form_data['is_superuser'] and self.user_to_modify.is_superuser and len(User.objects.filter(is_superuser=True) ) == 1:
            self.add_error("is_superuser", "nel sistema ci deve essere almeno un super utente")

        your_password = self.cleaned_data.get('your_password', None)
        if not your_password or not self.user.check_password(your_password):
            self.add_error("your_password", "Password Errata")  # Will raise a error message
            del form_data['your_password']


        return form_data





class UserForgotPasswordForm(forms.Form):
    email_or_username = forms.CharField(required=True, max_length=254)

    def __init__(self, data=None, files=None, recipient_list=None, *args, **kwargs):
        super().__init__(data=data, files=files, *args, **kwargs)
        self.fields['email_or_username'].widget.attrs['class'] = 'input100'


    def clean(self):
        email_or_username = self.cleaned_data.get('email_or_username', None)
        user = User.objects.filter(Q(email=email_or_username) | Q(username=email_or_username)).first()
        if user is None:
            self.add_error("email_or_username","utente non registrato")  # Will raise a error message
            del self.cleaned_data['email_or_username']


class ResetPasswordForm(forms.Form):
    password = forms.CharField(label='Password', max_length=50,
                               widget=forms.PasswordInput(), required=True)
    confirm_password = forms.CharField(label='Conferma la Password', max_length=50,
                               widget=forms.PasswordInput(), required=True)

    layout = Layout('password', 'confirm_password')

    def __init__(self, data=None, files=None, recipient_list=None, *args, **kwargs):
        super().__init__(data=data, files=files, *args, **kwargs)


    def clean(self):
        form_data = self.cleaned_data
        password = self.cleaned_data.get('password', None)
        confirm_password = self.cleaned_data.get('confirm_password', None)
        if password != confirm_password:
            self.add_error("password","La Password non Corrisponde")  # Will raise a error message
            del form_data['password']
            del form_data['confirm_password']




class CreateExternalUser(forms.ModelForm):
    name = forms.CharField(label='Nome', max_length=50,
                           widget=forms.TextInput(attrs={'placeholder': 'Nome'}))
    timedelta = forms.IntegerField(label='durata in ore',min_value=0, required=True,
                                   widget=forms.NumberInput(attrs={'value': '8'}))
    email = forms.EmailField(required=False)

    def __init__(self,smartglass=None, data=None, files=None, recipient_list=None, *args, **kwargs):
        super().__init__(data=data, files=files, *args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['smartGlass'].widget.attrs['class'] = 'form-control'
        if smartglass:
         self.fields['smartGlass'].initial = smartglass



    class Meta:
    #    model = ExternalUser
        fields = ('name', 'smartGlass','email')

