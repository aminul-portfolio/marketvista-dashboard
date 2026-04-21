from django import forms
from .models import Trade

from django import forms
# ✅ For creating trades
from django import forms
from .models import Trade

class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = ["asset", "trade_type", "entry_price", "quantity", "notes"]
        widgets = {
            "asset": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Select Asset"
            }),
            "trade_type": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Buy or Sell"
            }),
            "entry_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Entry Price"
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Quantity"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Any notes...",
                "rows": 3
            }),
        }
        labels = {
            "asset": "Asset Symbol",
            "trade_type": "Trade Type",
            "entry_price": "Entry Price ($)",
            "quantity": "Quantity",
            "notes": "Trade Notes",
        }


# ✅ For all risk calculations
from django import forms


class UnifiedRiskForm(forms.Form):
    MODE_CHOICES = [
        ("volume", "Volume for Target Risk"),
        ("stoploss", "Stop Loss for Target Risk"),
        ("target", "Target Price for Desired Profit"),
        ("riskreward", "Risk/Reward Metrics"),
        ("riskpercent", "Max Volume for % Account Risk"),
        ("targetprofitvolume", "Volume to Achieve Desired Profit at Target Price")
    ]

    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        widget=forms.RadioSelect,
        label="Select Calculator Mode"
    )

    account_size = forms.DecimalField(
        label="Account Size (£)",
        decimal_places=2,
        max_digits=12,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 10,000"})
    )

    risk_percent = forms.DecimalField(
        label="Risk % of Account",
        decimal_places=2,
        max_digits=5,
        required=False,
        help_text="Example: 2 means 2% risk."
    )

    risk_amount = forms.DecimalField(
        label="Risk Amount (£)",
        decimal_places=2,
        max_digits=12,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 100"})
    )

    desired_profit = forms.DecimalField(
        label="Desired Profit (£)",
        decimal_places=2,
        max_digits=12,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 200"})
    )

    entry_price = forms.DecimalField(
        label="Entry Price",
        decimal_places=5,
        max_digits=12,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 1.2345"})
    )

    stop_loss_price = forms.DecimalField(
        label="Stop Loss Price",
        decimal_places=5,
        max_digits=12,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 1.2000"})
    )

    target_price = forms.DecimalField(
        label="Target Price",
        decimal_places=5,
        max_digits=12,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 1.3000"})
    )

    volume = forms.DecimalField(
        label="Volume",
        decimal_places=4,
        max_digits=12,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 0.5"})
    )


from django import forms
from .models import Alert

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