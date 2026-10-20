from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
    path("transactions/", views.transactions, name="transactions"),
    path("insights/", views.insights, name="insights"),
    path("budget/", views.save_budget, name="save_budget"),
    path(
        "transactions/<int:expense_id>/delete/",
        views.delete_transaction,
        name="delete_transaction",
    ),
    path("signup/", views.signup, name="signup"),
]