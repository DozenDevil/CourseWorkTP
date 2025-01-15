from flask import Flask
from .model import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'  # Путь к базе данных
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # Создаём все таблицы, если их нет
        db.create_all()

        # Регистрация маршрутов
        from .controller import init_routes
        init_routes(app)

    return app
