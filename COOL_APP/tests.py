from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Expense, MonthlyBudget


class DashboardTests(TestCase):
    def test_dashboard_renders_empty_state(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your spending story starts here.")
        self.assertContains(response, "Add your first expense to see your spending breakdown.")
        self.assertNotContains(response, "Spending Calendar")

    def test_navigation_pages_are_separate(self):
        transactions_response = self.client.get(reverse("transactions"))
        insights_response = self.client.get(reverse("insights"))

        self.assertEqual(transactions_response.status_code, 200)
        self.assertContains(transactions_response, "Manage Transactions")
        self.assertContains(transactions_response, "Search transactions")
        self.assertNotContains(transactions_response, "Spending Calendar")
        self.assertContains(transactions_response, 'href="/insights/"')
        self.assertContains(transactions_response, 'href="/"')
        self.assertEqual(insights_response.status_code, 200)
        self.assertContains(insights_response, "Spending Calendar")
        self.assertContains(insights_response, "Where your money goes")
        self.assertNotContains(insights_response, "Manage Transactions")

    def test_insights_day_link_filter_is_supported(self):
        response = self.client.get(
            reverse("transactions"), {"from": "2026-10-06", "to": "2026-10-06"}
        )

        self.assertContains(response, 'id="filter-from" value="2026-10-06"')
        self.assertContains(response, 'id="filter-to" value="2026-10-06"')

    def test_dashboard_shows_user_expense_totals(self):
        user = User.objects.create_user(username="mikaela", password="pass1234")
        Expense.objects.create(
            amount="125.50",
            category="Food",
            description="Lunch",
            date=date.today(),
            payment_method="Cash",
            user=user,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "₱125.50")
        self.assertContains(response, "Lunch")
        self.assertContains(response, "Food")

    def test_authenticated_user_can_add_an_expense(self):
        user = User.objects.create_user(username="mikaela", password="pass1234")
        self.client.force_login(user)

        response = self.client.post(
            reverse("dashboard"),
            {
                "amount": "80.00",
                "category": "Transportation",
                "description": "Bus ride",
                "date": date.today().isoformat(),
                "payment_method": "Cash",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(Expense.objects.filter(user=user, description="Bus ride").exists())

    def test_income_and_monthly_budget_are_saved_and_shown(self):
        user = User.objects.create_user(username="budget-test", password="test-password")
        self.client.force_login(user)

        response = self.client.post(
            reverse("dashboard"),
            {
                "transaction_type": "income",
                "amount": "2500.00",
                "category": "Other",
                "description": "Pay",
                "date": date.today().isoformat(),
                "payment_method": "Bank Transfer",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.client.post(reverse("save_budget"), {"amount": "3000.00"})

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(MonthlyBudget.objects.get(user=user).amount, 3000)
        self.assertTrue(
            Expense.objects.filter(
                user=user,
                transaction_type=Expense.TYPE_INCOME,
                amount=2500,
                description="Pay",
            ).exists()
        )
        self.assertContains(response, "INCOME")
        self.assertContains(response, "Pay")
        self.assertContains(response, "MONTHLY BUDGET")

    def test_transaction_validation_edit_and_delete(self):
        user = User.objects.create_user(username="manage-test", password="test-password")
        self.client.force_login(user)

        invalid_response = self.client.post(
            reverse("dashboard"),
            {
                "transaction_type": "expense",
                "amount": "-1",
                "category": "",
                "description": "Invalid",
                "date": date.today().isoformat(),
                "payment_method": "Cash",
            },
        )
        self.assertContains(invalid_response, "Please enter a valid amount.")
        self.assertContains(invalid_response, "Please select a category.")
        transaction = Expense.objects.create(
            amount="100.00",
            category="Food",
            description="Lunch",
            date=date.today(),
            payment_method="Cash",
            user=user,
        )

        edit_response = self.client.post(
            reverse("dashboard"),
            {
                "expense_id": transaction.expense_id,
                "transaction_type": "expense",
                "amount": "150.00",
                "category": "Shopping",
                "description": "Groceries",
                "date": date.today().isoformat(),
                "payment_method": "Debit Card",
            },
        )
        self.assertRedirects(edit_response, reverse("dashboard"))
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, 150)
        self.assertEqual(transaction.category, "Shopping")

        delete_response = self.client.post(
            reverse("delete_transaction", args=[transaction.expense_id])
        )
        self.assertRedirects(delete_response, reverse("transactions"))
        self.assertFalse(Expense.objects.filter(expense_id=transaction.expense_id).exists())

# Create your tests here.
