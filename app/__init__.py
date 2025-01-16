from flask import Flask
from .model import db


def create_app():
    app = Flask(__name__)

    # Настройки
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MODEL_FOLDER'] = 'static/models'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        # Создаём все таблицы, если их нет
        db.create_all()

        # Регистрация маршрутов
        from .controller import init_routes
        init_routes(app)

    return app
