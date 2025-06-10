from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, Usuario
from routes import main  

login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app(test_config=None):
    app = Flask(__name__)

    if test_config:
        app.config.from_object(test_config)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(main)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    return app

