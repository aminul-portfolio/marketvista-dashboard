from django import forms
from .models import Alert

class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ["asset", "direction", "target_price"]
        widgets = {
            "asset": forms.Select(attrs={"class": "form-select"}),
            "direction": forms.Select(attrs={"class": "form-select"}),
            "target_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
        }