# forms.py
from django import forms
from .models import Client

class OrganizationForm(forms.ModelForm):
    client_name = forms.CharField(strip=True)
    state = forms.ChoiceField(choices=Client.STATE_LIST)

    class Meta:
        model = Client
        fields = ['client_name', 'address1', 'address2', 'city', 'state', 'zip_code']
