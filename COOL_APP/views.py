from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BudgetForm, ExpenseForm
from .models import Expense, MonthlyBudget

# Create your views here.
def index(request, template_name="index.html"):
    expenses = Expense.objects.none()
    if request.user.is_authenticated:
        expenses = Expense.objects.filter(user=request.user)

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Sign in before adding an expense.")
            return redirect("dashboard")
        expense_id = request.POST.get("expense_id")
        instance = None
        if expense_id:
            instance = get_object_or_404(
                Expense, expense_id=expense_id, user=request.user
            )
        form = ExpenseForm(request.POST, instance=instance)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            action = "updated" if instance else "added"
            messages.success(request, f"Transaction {action} to your dashboard.")
            return redirect("dashboard")
    else:
        edit_id = request.GET.get("edit")
        edit_instance = (
            get_object_or_404(Expense, expense_id=edit_id, user=request.user)
            if edit_id and request.user.is_authenticated
            else None
        )
        form = ExpenseForm(
            instance=edit_instance,
            initial={"date": date.today(), "transaction_type": Expense.TYPE_EXPENSE}
            if edit_instance is None
            else None,
        )

    today = timezone.localdate()
    month_expenses = expenses.filter(
        transaction_type=Expense.TYPE_EXPENSE,
        date__year=today.year,
        date__month=today.month,
    )
    total_expenses = (
        expenses.filter(transaction_type=Expense.TYPE_EXPENSE).aggregate(total=Sum("amount"))[
            "total"
        ]
        or Decimal("0.00")
    )
    total_income = (
        expenses.filter(transaction_type=Expense.TYPE_INCOME).aggregate(total=Sum("amount"))[
            "total"
        ]
        or Decimal("0.00")
    )
    month_spent = month_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    month_transaction_count = expenses.filter(
        date__year=today.year, date__month=today.month
    ).count()
    category_totals = list(
        expenses.filter(transaction_type=Expense.TYPE_EXPENSE)
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    category_sum = sum((item["total"] for item in category_totals), Decimal("0.00"))
    category_icons = {
        "Food": "🍔",
        "Transportation": "🚗",
        "Education": "📚",
        "Shopping": "🛍️",
        "Health": "💊",
        "Bills": "🏠",
        "Entertainment": "🎮",
        "Utilities": "📱",
        "Other": "💰",
    }
    for item in category_totals:
        item["percentage"] = (
            item["total"] / category_sum * 100 if category_sum else Decimal("0")
        )
        item["icon"] = category_icons.get(item["category"], "💰")

    all_transactions = list(expenses.order_by("-date", "-expense_id"))
    recent_expenses = all_transactions[:8]
    budget = (
        MonthlyBudget.objects.filter(user=request.user).first()
        if request.user.is_authenticated
        else None
    )
    budget_amount = budget.amount if budget else Decimal("0.00")
    budget_used = (
        month_spent / budget_amount * 100 if budget_amount > 0 else Decimal("0")
    )
    top_category = category_totals[0]["category"] if category_totals else "No category yet"
    hour = timezone.localtime().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    display_name = (
        request.user.first_name or request.user.username
        if request.user.is_authenticated
        else "there"
    )
    local_storage_data = {
        "budget": str(budget_amount),
        "transactions": [
            {
                "id": transaction.expense_id,
                "type": transaction.transaction_type,
                "amount": str(transaction.amount),
                "category": transaction.category,
                "description": transaction.description,
                "date": transaction.date.isoformat(),
                "payment_method": transaction.payment_method,
            }
            for transaction in all_transactions
        ],
    }

    return render(
        request,
        template_name,
        {
            "form": form,
            "total_spent": total_expenses,
            "total_income": total_income,
            "remaining": total_income - total_expenses,
            "month_spent": month_spent,
            "transaction_count": expenses.count(),
            "budget_amount": budget_amount,
            "budget_used": budget_used,
            "budget_remaining": budget_amount - month_spent,
            "budget_transaction_count": month_transaction_count,
            "within_budget": budget_amount > 0 and month_spent <= budget_amount,
            "budget_progress": min(budget_used, Decimal("100")),
            "top_category": top_category,
            "category_totals": category_totals,
            "recent_expenses": recent_expenses,
            "all_transactions": all_transactions,
            "current_month": today.strftime("%B"),
            "today_iso": today.isoformat(),
            "budget_form": BudgetForm(initial={"amount": budget_amount} if budget else None),
            "editing_expense_id": request.POST.get("expense_id", "")
            or (request.GET.get("edit", "") if request.user.is_authenticated else ""),
            "is_editing": bool(request.POST.get("expense_id") or request.GET.get("edit")),
            "greeting": greeting,
            "display_name": display_name,
            "local_storage_data": local_storage_data,
            "active_page": {
                "index.html": "home",
                "transactions.html": "transactions",
                "insights.html": "insights",
            }[template_name],
            "page_title": {
                "index.html": "Home",
                "transactions.html": "Transactions",
                "insights.html": "Insights",
            }[template_name],
            "page_subtitle": {
                "index.html": f"Here's your spending overview for {today.strftime('%B')}.",
                "transactions.html": "Search, review, and manage your transactions.",
                "insights.html": "Explore your spending patterns and monthly activity.",
            }[template_name],
            "filter_from": request.GET.get("from", ""),
            "filter_to": request.GET.get("to", ""),
        },
    )


def transactions(request):
    return index(request, "transactions.html")


def insights(request):
    response = index(request, "insights.html")
    return response


def save_budget(request):
    if not request.user.is_authenticated:
        messages.error(request, "Sign in before setting a monthly budget.")
        return redirect("signup")
    if request.method != "POST":
        return redirect("dashboard")

    form = BudgetForm(request.POST)
    if form.is_valid():
        MonthlyBudget.objects.update_or_create(
            user=request.user, defaults={"amount": form.cleaned_data["amount"]}
        )
        messages.success(request, "Monthly budget saved.")
    else:
        messages.error(request, "Please enter a valid budget.")
    return redirect("dashboard")


def delete_transaction(request, expense_id):
    if not request.user.is_authenticated:
        messages.error(request, "Sign in before managing transactions.")
        return redirect("signup")
    if request.method == "POST":
        expense = get_object_or_404(
            Expense, expense_id=expense_id, user=request.user
        )
        expense.delete()
        messages.success(request, "Transaction deleted.")
    return redirect("transactions")


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your BudgetBuddy account is ready.")
        return redirect("dashboard")

    return render(request, "registration/signup.html", {"form": form})