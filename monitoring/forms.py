from django import forms

from .models import Alert


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ["asset", "direction", "target_price"]
        widgets = {
            "asset": forms.Select(attrs={"class": "mv-ca-field"}),
            "direction": forms.Select(attrs={"class": "mv-ca-field"}),
            "target_price": forms.NumberInput(
                attrs={
                    "class": "mv-ca-field",
                    "step": "0.0001",
                    "placeholder": "Enter target price",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].empty_label = "Select an asset"

    def clean_target_price(self):
        value = self.cleaned_data["target_price"]
        if value is None:
            raise forms.ValidationError("Target price is required.")
        if value <= 0:
            raise forms.ValidationError("Target price must be greater than 0.")
        return value