from django import forms

from .models import Expense

CATEGORY_CHOICES = (
    ("Food", "🍔 Food"),
    ("Transportation", "🚗 Transportation"),
    ("Education", "📚 Education"),
    ("Shopping", "🛍️ Shopping"),
    ("Health", "💊 Health"),
    ("Bills", "🏠 Bills"),
    ("Entertainment", "🎮 Entertainment"),
    ("Utilities", "📱 Utilities"),
    ("Other", "💰 Other"),
)
PAYMENT_METHOD_CHOICES = (
    ("Cash", "💵 Cash"),
    ("Debit Card", "💳 Debit Card"),
    ("Credit Card", "💳 Credit Card"),
    ("Bank Transfer", "🏦 Bank Transfer"),
    ("GCash", "📱 GCash"),
    ("Maya", "📱 Maya"),
    ("Other", "Other"),
)


class ExpenseForm(forms.ModelForm):
    CATEGORY_CHOICES = CATEGORY_CHOICES
    PAYMENT_METHOD_CHOICES = PAYMENT_METHOD_CHOICES

    transaction_type = forms.ChoiceField(
        choices=(("", "Choose type"),) + Expense.TRANSACTION_TYPE_CHOICES,
        required=False,
    )
    category = forms.ChoiceField(
        choices=(("", "Select a category"),) + CATEGORY_CHOICES,
        error_messages={"required": "Please select a category."},
    )
    payment_method = forms.ChoiceField(
        choices=(("", "Select a payment method"),) + PAYMENT_METHOD_CHOICES
    )
    amount = forms.DecimalField(
        min_value=0.01,
        error_messages={
            "required": "Please enter a valid amount.",
            "invalid": "Please enter a valid amount.",
            "min_value": "Please enter a valid amount.",
        },
        widget=forms.NumberInput(
            attrs={"placeholder": "0.00", "step": "0.01", "min": "0.01"}
        ),
    )

    class Meta:
        model = Expense
        fields = (
            "transaction_type",
            "amount",
            "category",
            "description",
            "date",
            "payment_method",
        )
        widgets = {
            "amount": forms.NumberInput(
                attrs={"placeholder": "0.00", "step": "0.01", "min": "0.01"}
            ),
            "description": forms.TextInput(attrs={"placeholder": "What was this for?"}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "payment_method": forms.Select(choices=PAYMENT_METHOD_CHOICES),
        }

    def clean_transaction_type(self):
        transaction_type = self.cleaned_data.get("transaction_type") or Expense.TYPE_EXPENSE
        if transaction_type not in dict(Expense.TRANSACTION_TYPE_CHOICES):
            raise forms.ValidationError("Please select a transaction type.")
        return transaction_type


class BudgetForm(forms.Form):
    amount = forms.DecimalField(
        min_value=0.01,
        error_messages={
            "required": "Please enter a valid budget.",
            "invalid": "Please enter a valid budget.",
            "min_value": "Please enter a valid budget.",
        },
        widget=forms.NumberInput(
            attrs={"placeholder": "Set monthly budget", "step": "0.01", "min": "0.01"}
        ),
    )
