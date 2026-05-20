from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class RegisterForm(forms.ModelForm):
    # Keep the ModelForm around for any admin/legacy usage, but registration
    # UI now uses a single "identifier" field handled in the view. We only
    # validate password strength here when used.
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = CustomUser
        fields = ["email", "username", "password", "phone"]

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password)
        return password

class LoginForm(AuthenticationForm):
    # Accept either email or username as an identifier for login
    identifier = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Email or Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
            