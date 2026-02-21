from flask import Flask
from extensions import db
import os

# 🔹 IMPORT BLUEPRINTS (TOP PART)
from routes.transactions import transactions_bp
from routes.home import home_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.budgets import budgets_bp
from routes.analytics import analytics_bp
from routes.tools import tools_bp
from routes.settings import settings_bp
from routes.goals import goals_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "secret123"

    app.config['SQLALCHEMY_DATABASE_URI'] = \
        'sqlite:///' + os.path.join(app.instance_path, 'database.db')

    db.init_app(app)

    # 🔹 REGISTER BLUEPRINTS (INSIDE create_app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(settings_bp)
   

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)