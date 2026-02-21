from flask import Blueprint, render_template, session, redirect, url_for
from collections import defaultdict
from statistics import pstdev
from models import Transaction, Budget

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics")
def analytics():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    # ---------------- Monthly analytics ----------------
    monthly_data = defaultdict(lambda: {"income": 0, "expense": 0})
    for t in transactions:
        month = t.date.strftime("%Y-%m")
        monthly_data[month][t.type] += t.amount

    # ---------------- Category-wise expense ----------------
    category_expense = defaultdict(float)
    for t in transactions:
        if t.type == "expense":
            category_expense[t.category.strip().lower()] += t.amount

    # ---------------- Totals ----------------
    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expense = sum(t.amount for t in transactions if t.type == "expense")

    # =====================================================
    # 📊 OVERALL FINANCIAL HEALTH SCORE
    # =====================================================
    score = 0
    insights = []

    # 1️⃣ Savings Rate (30)
    if total_income > 0:
        savings_rate = (total_income - total_expense) / total_income
        savings_score = min(max(savings_rate * 30, 0), 30)
    else:
        savings_rate = 0
        savings_score = 0

    score += savings_score
    if savings_rate < 0.2:
        insights.append("Try to save at least 20% of your income.")

    # 2️⃣ Expense Control (25)
    expense_ratio = total_expense / total_income if total_income else 1
    expense_score = 25 if expense_ratio <= 0.7 else max(0, 25 - ((expense_ratio - 0.7) * 50))
    score += expense_score

    if expense_ratio > 0.7:
        insights.append("Your expenses are high compared to income.")

    # 3️⃣ Budget Discipline (25)
    budgets = Budget.query.filter_by(user_id=user_id).all()
    budget_score = 25

    for b in budgets:
        spent = category_expense.get(b.category.strip().lower(), 0)
        if spent > b.amount:
            budget_score -= 5

    budget_score = max(budget_score, 0)
    score += budget_score

    if budget_score < 25:
        insights.append("Some budgets were exceeded.")

    # 4️⃣ Income Stability (20)
    income_values = [v["income"] for v in monthly_data.values() if v["income"] > 0]

    if len(income_values) > 1:
        volatility = pstdev(income_values)
        stability_score = max(0, 20 - (volatility / max(income_values)) * 20)
    else:
        stability_score = 10

    score += stability_score

    if stability_score < 10:
        insights.append("Your income varies significantly month to month.")

    health_score = round(score)

    if health_score >= 80:
        health_status = "Excellent 💚"
    elif health_score >= 60:
        health_status = "Good 💛"
    elif health_score >= 40:
        health_status = "Needs Improvement 🧡"
    else:
        health_status = "Poor ❤️"

    # =====================================================
    # 📈 MONTHLY FINANCIAL HEALTH TREND
    # =====================================================
    monthly_health = {}

    for month, data in monthly_data.items():
        income = data["income"]
        expense = data["expense"]

        if income <= 0:
            monthly_health[month] = 0
            continue

        savings_rate = (income - expense) / income
        savings_score = min(max(savings_rate * 50, 0), 50)

        expense_ratio = expense / income
        expense_score = 50 if expense_ratio <= 0.7 else max(
            0, 50 - ((expense_ratio - 0.7) * 100)
        )

        monthly_health[month] = round(savings_score + expense_score)

    return render_template(
        "analytics.html",
        monthly_data=dict(monthly_data),
        category_expense=dict(category_expense),
        total_income=total_income,
        total_expense=total_expense,
        health_score=health_score,
        health_status=health_status,
        insights=insights,
        monthly_health=monthly_health
    )
