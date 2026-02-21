from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from extensions import db
from models import SavingsGoal
from datetime import datetime, date

goals_bp = Blueprint("goals", __name__)


@goals_bp.route("/goals")
def goals_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    goals = SavingsGoal.query.filter_by(user_id=user_id).order_by(SavingsGoal.completed, SavingsGoal.target_date).all()

    goals_data = []
    for goal in goals:
        # Calculate progress
        percentage = min(int((goal.current_amount / goal.target_amount) * 100), 100) if goal.target_amount > 0 else 0
        remaining_amount = max(goal.target_amount - goal.current_amount, 0)
        
        # Calculate days remaining
        days_remaining = (goal.target_date - date.today()).days
        
        # Calculate monthly savings needed
        if days_remaining > 0 and remaining_amount > 0:
            months_remaining = days_remaining / 30.44  # Average days per month
            monthly_needed = remaining_amount / months_remaining if months_remaining > 0 else remaining_amount
        else:
            monthly_needed = 0
        
        # Determine status
        if goal.completed:
            status = "✅ Completed"
            status_color = "#00d4aa"
        elif percentage >= 100:
            status = "🎉 Goal Reached!"
            status_color = "#00d4aa"
        elif days_remaining < 0:
            status = "⏰ Overdue"
            status_color = "#ff6b6b"
        elif days_remaining < 30:
            status = "⚠️ Urgent"
            status_color = "#ffb84d"
        else:
            # Calculate if on track
            expected_progress = ((date.today() - goal.created_at.date()).days / 
                               (goal.target_date - goal.created_at.date()).days * 100) if goal.created_at else 0
            
            if percentage >= expected_progress - 5:
                status = "🟢 On Track"
                status_color = "#00d4aa"
            elif percentage >= expected_progress - 15:
                status = "🟡 Behind Schedule"
                status_color = "#ffb84d"
            else:
                status = "🔴 Needs Attention"
                status_color = "#ff6b6b"
        
        goals_data.append({
            "id": goal.id,
            "name": goal.name,
            "icon": goal.icon,
            "color": goal.color,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "percentage": percentage,
            "remaining_amount": remaining_amount,
            "target_date": goal.target_date.strftime("%b %d, %Y"),
            "days_remaining": max(days_remaining, 0),
            "monthly_needed": monthly_needed,
            "status": status,
            "status_color": status_color,
            "completed": goal.completed
        })

    return render_template("goals.html", goals=goals_data)


@goals_bp.route("/add_goal", methods=["POST"])
def add_goal():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    
    try:
        new_goal = SavingsGoal(
            user_id=user_id,
            name=request.form["name"],
            target_amount=float(request.form["target_amount"]),
            current_amount=float(request.form.get("current_amount", 0)),
            target_date=datetime.strptime(request.form["target_date"], "%Y-%m-%d").date(),
            icon=request.form.get("icon", "🎯"),
            color=request.form.get("color", "#00d4aa")
        )
        
        db.session.add(new_goal)
        db.session.commit()
        
        flash(f"✅ Goal '{new_goal.name}' created successfully!", "success")
    except Exception as e:
        flash(f"❌ Error creating goal: {str(e)}", "error")
    
    return redirect(url_for("goals.goals_page"))


@goals_bp.route("/update_goal/<int:goal_id>", methods=["POST"])
def update_goal(goal_id):
    if "user_id" not in session:
        return {"error": "unauthorized"}, 401

    goal = SavingsGoal.query.get_or_404(goal_id)
    
    if goal.user_id != session["user_id"]:
        return {"error": "forbidden"}, 403

    try:
        data = request.get_json()
        
        if "name" in data:
            goal.name = data["name"]
        if "target_amount" in data:
            goal.target_amount = float(data["target_amount"])
        if "current_amount" in data:
            goal.current_amount = float(data["current_amount"])
        if "target_date" in data:
            goal.target_date = datetime.strptime(data["target_date"], "%Y-%m-%d").date()
        if "icon" in data:
            goal.icon = data["icon"]
        if "color" in data:
            goal.color = data["color"]
        
        db.session.commit()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}, 400


@goals_bp.route("/add_contribution/<int:goal_id>", methods=["POST"])
def add_contribution(goal_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    goal = SavingsGoal.query.get_or_404(goal_id)
    
    if goal.user_id != session["user_id"]:
        flash("❌ Unauthorized access", "error")
        return redirect(url_for("goals.goals_page"))

    try:
        amount = float(request.form["amount"])
        goal.current_amount += amount
        
        # Check if goal is reached
        if goal.current_amount >= goal.target_amount and not goal.completed:
            goal.completed = True
            flash(f"🎉 Congratulations! You've reached your goal: {goal.name}!", "success")
        else:
            flash(f"✅ Added ₹{amount:,.2f} to '{goal.name}'", "success")
        
        db.session.commit()
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
    
    return redirect(url_for("goals.goals_page"))


@goals_bp.route("/mark_complete/<int:goal_id>")
def mark_complete(goal_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    goal = SavingsGoal.query.get_or_404(goal_id)
    
    if goal.user_id != session["user_id"]:
        flash("❌ Unauthorized access", "error")
        return redirect(url_for("goals.goals_page"))

    goal.completed = not goal.completed
    db.session.commit()
    
    status = "completed" if goal.completed else "reopened"
    flash(f"✅ Goal '{goal.name}' {status}!", "success")
    
    return redirect(url_for("goals.goals_page"))


@goals_bp.route("/delete_goal/<int:goal_id>")
def delete_goal(goal_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    goal = SavingsGoal.query.get_or_404(goal_id)
    
    if goal.user_id != session["user_id"]:
        flash("❌ Unauthorized access", "error")
        return redirect(url_for("goals.goals_page"))

    goal_name = goal.name
    db.session.delete(goal)
    db.session.commit()
    
    flash(f"🗑️ Goal '{goal_name}' deleted", "success")
    
    return redirect(url_for("goals.goals_page"))