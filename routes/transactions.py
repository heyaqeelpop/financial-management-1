import csv
from flask import Blueprint, redirect, url_for, request, session, Response, flash
from datetime import datetime

from extensions import db
from models import Transaction

transactions_bp = Blueprint("transactions", __name__)


from flask import render_template
                                                #newly added
@transactions_bp.route("/ledger")
def ledger():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # 🔎 Filters from query params
    category = request.args.get("category")
    txn_type = request.args.get("type")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Base query
    query = Transaction.query.filter_by(user_id=user_id)

    # Apply filters dynamically
    if category:
        query = query.filter(Transaction.category.ilike(f"%{category}%"))

    if txn_type in ["income", "expense"]:
        query = query.filter(Transaction.type == txn_type)

    if start_date:
        query = query.filter(
            Transaction.date >= datetime.strptime(start_date, "%Y-%m-%d").date()
        )

    if end_date:
        query = query.filter(
            Transaction.date <= datetime.strptime(end_date, "%Y-%m-%d").date()
        )

    transactions = query.order_by(Transaction.date.desc()).all()

    return render_template(
        "ledger.html",
        transactions=transactions,
        filters={
            "category": category or "",
            "type": txn_type or "",
            "start_date": start_date or "",
            "end_date": end_date or ""
        }
    )




# ➕ Add Transaction
@transactions_bp.route("/add_transaction", methods=["POST"])
def add_transaction():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    txn = Transaction(
        amount=float(request.form["amount"]),
        category=request.form["category"].strip().lower(),
        type=request.form["type"],
        date=datetime.strptime(request.form["date"], "%Y-%m-%d").date(),
        user_id=session["user_id"]
    )

    db.session.add(txn)
    db.session.commit()

    return redirect(url_for("transactions.ledger"))


# ❌ Delete Transaction
@transactions_bp.route("/delete/<int:id>")
def delete_transaction(id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    txn = Transaction.query.get_or_404(id)

    if txn.user_id != session["user_id"]:
        return redirect(url_for("transactions.ledger"))

    db.session.delete(txn)
    db.session.commit()

    return redirect(url_for("transactions.ledger"))


@transactions_bp.route("/update_transaction/<int:id>", methods=["POST"])
def update_transaction(id):
    if "user_id" not in session:
        return {"error": "unauthorized"}, 401

    txn = Transaction.query.get_or_404(id)

    if txn.user_id != session["user_id"]:
        return {"error": "forbidden"}, 403

    data = request.get_json()

    txn.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    txn.type = data["type"]
    txn.category = data["category"].strip().lower()
    txn.amount = float(data["amount"])

    db.session.commit()

    return {"success": True}



@transactions_bp.route("/delete_all", methods=["POST"])
def delete_all_transactions():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    Transaction.query.filter_by(
        user_id=session["user_id"]
    ).delete()

    db.session.commit()

    flash("🗑️ All transactions deleted successfully", "success")
    return redirect(url_for("transactions.ledger"))



# ⬇ Export CSV
@transactions_bp.route("/export")
def export_csv():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    transactions = Transaction.query.filter_by(
        user_id=session["user_id"]
    ).all()

    def generate():
        yield "ID,Type,Category,Amount,Date\n"
        for t in transactions:
            yield f"{t.id},{t.type},{t.category},{t.amount},{t.date}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )


# ⬆ Import CSV
@transactions_bp.route("/import_csv", methods=["POST"])
def import_csv():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    file = request.files.get("file")

    if not file or not file.filename.endswith(".csv"):
        flash("❌ Invalid CSV file", "error")
        return redirect(url_for("transactions.ledger"))

    reader = csv.DictReader(
        file.stream.read().decode("utf-8").splitlines()
    )

    required = {"type", "amount", "category", "date"}
    if not required.issubset(reader.fieldnames):
        flash("❌ CSV columns incorrect", "error")
        return redirect(url_for("transactions.ledger"))

    count = 0
    for row in reader:
        try:
            txn = Transaction(
                type=row["type"].lower(),
                amount=float(row["amount"]),
                category=row["category"].strip().lower(),
                date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                user_id=session["user_id"]
            )
            db.session.add(txn)
            count += 1
        except Exception:
            continue

    db.session.commit()
    flash(f"✅ {count} transactions imported", "success")

    return redirect(url_for("transactions.ledger"))

