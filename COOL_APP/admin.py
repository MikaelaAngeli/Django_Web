from django.contrib import admin
from .models import Expense, MonthlyBudget
#register your models here.
admin.site.register(Expense)
admin.site.register(MonthlyBudget)