from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Expense(models.Model):
    TYPE_EXPENSE = "expense"
    TYPE_INCOME = "income"
    TRANSACTION_TYPE_CHOICES = (
        (TYPE_EXPENSE, "Expense"),
        (TYPE_INCOME, "Income"),
    )

    expense_id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    payment_method = models.CharField(max_length=50)
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES, default=TYPE_EXPENSE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.category} -₱{self.amount}"

    @property
    def category_icon(self):
        return {
            "Food": "🍔",
            "Transportation": "🚗",
            "Education": "📚",
            "Shopping": "🛍️",
            "Health": "💊",
            "Bills": "🏠",
            "Entertainment": "🎮",
            "Utilities": "📱",
            "Other": "💰",
        }.get(self.category, "💰")


class MonthlyBudget(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}'s monthly budget: ₱{self.amount}"