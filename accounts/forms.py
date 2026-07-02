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

class ChangePasswordForm(forms.Form):
    """Form for changing password on client-side UI."""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Current Password',
            'class': 'auth-input'
        }),
        label='Current Password'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'New Password',
            'class': 'auth-input'
        }),
        label='New Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm New Password',
            'class': 'auth-input'
        }),
        label='Confirm New Password'
    )

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            validate_password(new_password)
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('New passwords do not match.')
        
        return cleaned_data
            