from django import forms

class InstagramLoginForm(forms.Form):
    username = forms.CharField(max_length=100, label='Instagram Username')
    password = forms.CharField(widget=forms.PasswordInput(), label='Instagram Password')