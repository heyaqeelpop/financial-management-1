from flask import Blueprint, render_template, session, redirect, url_for, request
from collections import defaultdict
from datetime import date
from models import Transaction, Budget

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    # ---------------- Monthly analytics ----------------
    monthly_data = defaultdict(lambda: {"income": 0, "expense": 0})
    for t in transactions:
        month = t.date.strftime("%Y-%m")
        monthly_data[month][t.type] += t.amount

    # ---------------- Category-wise expense ----------------
    selected_month = request.args.get("month")  # YYYY-MM or None
    category_expense = defaultdict(float)

    for t in transactions:
        if t.type != "expense":
            continue

        # Only include selected month if user chose one
        if selected_month and t.date.strftime("%Y-%m") != selected_month:
            continue

        category_expense[t.category.strip().lower()] += t.amount

    # ---------------- Totals ----------------
    if selected_month:
        total_income = sum(
            t.amount for t in transactions
            if t.type == 'income' and t.date.strftime("%Y-%m") == selected_month
        )
        total_expense = sum(
            t.amount for t in transactions
            if t.type == 'expense' and t.date.strftime("%Y-%m") == selected_month
        )
    else:
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expense = sum(t.amount for t in transactions if t.type == 'expense')

    balance = total_income - total_expense

    # ---------------- Budgets (by selected month/year) ----------------
    if selected_month:
        sel_year, sel_month = map(int, selected_month.split("-"))
    else:
        today = date.today()
        sel_year, sel_month = today.year, today.month

    budgets = Budget.query.filter_by(
        user_id=user_id, month=sel_month, year=sel_year
    ).all()

    budget_data = []
    for b in budgets:
        spent = category_expense.get(b.category.strip().lower(), 0)
        percentage = int((spent / b.amount) * 100) if b.amount > 0 else 0
        budget_data.append({
            "category": b.category,
            "budget": b.amount,
            "spent": spent,
            "percentage": percentage
        })

    # ---------------- Render template ----------------
    return render_template(
        "dashboard.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        monthly_data=dict(monthly_data),
        category_expense=dict(category_expense),
        budget_data=budget_data,
        selected_month=selected_month,
        current_month=sel_month,
        current_year=sel_year
    )
