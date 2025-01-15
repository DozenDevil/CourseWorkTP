from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../instance/config.py', silent=True)

    with app.app_context():
        # Регистрация маршрутов
        from .controller import init_routes
        init_routes(app)

    return app
