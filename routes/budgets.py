# routes/budgets.py
from flask import Blueprint, request, redirect, url_for, session, flash, render_template
from extensions import db
from models import Budget, Transaction
from datetime import datetime
from sqlalchemy import func

budgets_bp = Blueprint("budgets", __name__)


@budgets_bp.route("/budgets")
def budgets_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Get all budgets for user
    budgets = Budget.query.filter_by(user_id=user_id).all()

    budget_data = []

    for b in budgets:
        # Calculate total spent for this category/month/year
        spent = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.category == b.category,
            Transaction.type == "expense",
            func.extract("month", Transaction.date) == b.month,
            func.extract("year", Transaction.date) == b.year
        ).scalar()

        percentage = min(int((spent / b.amount) * 100), 100) if b.amount > 0 else 0

        budget_data.append({
            "category": b.category.title(),
            "budget": b.amount,
            "spent": spent,
            "percentage": percentage,
            "month": b.month,
            "year": b.year
        })

    return render_template(
        "budgets.html",
        budget_data=budget_data
    )


@budgets_bp.route("/add_budget", methods=["POST"])
def add_budget():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    category = request.form["category"].strip().lower()
    amount = float(request.form["amount"])
    month = int(request.form["month"])
    year = int(request.form["year"])

    existing = Budget.query.filter_by(
        user_id=user_id,
        category=category,
        month=month,
        year=year
    ).first()

    if existing:
        existing.amount = amount
        flash(f"✅ Updated budget for {category} ({month}/{year})", "success")
    else:
        new_budget = Budget(
            user_id=user_id,
            category=category,
            amount=amount,
            month=month,
            year=year
        )
        db.session.add(new_budget)
        flash(f"✅ Set budget for {category} ({month}/{year})", "success")

    db.session.commit()
    return redirect(url_for("budgets.budgets_page"))
