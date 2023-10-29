# forms.py
from django import forms
from .models import Client, System

class OrganizationForm(forms.ModelForm):
    client_name = forms.CharField(strip=True)
    state = forms.ChoiceField(choices=Client.STATE_LIST)

    class Meta:
        model = Client
        fields = ['client_name', 'address1', 'address2', 'city', 'state', 'zip_code']

class SystemForm(forms.ModelForm):
    name = forms.CharField(strip=True)
    abbreviation = forms.CharField(strip=True, required=False)
    environment = forms.ChoiceField(choices=System.ENVIRONMENT_CHOICES, required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)
    authorization_boundary = forms.CharField(widget=forms.Textarea, required=False)
    operational_status = forms.ChoiceField(choices=System.OPERATIONAL_STATUS_CHOICES, required=False)
    last_authorization_date = forms.DateField(widget=forms.SelectDateWidget, required=False)
    fedramp_compliance_status = forms.ChoiceField(choices=System.FEDRAMP_COMPLIANCE_STATUS_CHOICES, required=False)
    owner_name = forms.CharField(strip=True, required=False)
    owner_title = forms.CharField(strip=True, required=False)
    owner_email = forms.EmailField(required=False)
    owner_phone_number = forms.CharField(required=False)
    color = forms.CharField(strip=True)

    class Meta:
        model = System
        fields = ['name', 'abbreviation', 'environment', 'description', 'authorization_boundary', 'operational_status', 
                  'last_authorization_date', 'fedramp_compliance_status', 'owner_name', 'owner_title', 'owner_email',
                  'owner_phone_number', 'client', 'color', 'information_subcategories']
