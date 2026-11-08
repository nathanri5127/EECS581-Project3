from flask import Flask
from flask_migrate import Migrate
from extensions import db
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.upload import upload_bp
from routes.analysis import analysis_bp

app = Flask(__name__)

app.config.from_object(
    "config.Config"
)

db.init_app(app)

migrate = Migrate(app, db)

app.register_blueprint(auth_bp)

app.register_blueprint(dashboard_bp)

app.register_blueprint(upload_bp)

app.register_blueprint(analysis_bp)

from flask_login import LoginManager
login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = ("auth.login")

from models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(
        debug=False
    )