from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Expense(models.Model):
    expense_id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    payment_method = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"expense_id: {self.category} -₱{self.amount}"