import pytest
from app import db, create_app
from app.model import ModelMetadata


@pytest.fixture(scope='module')
def setup_db():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Используем базу данных в памяти
    app.config['TESTING'] = True  # Включаем режим тестирования

    with app.app_context():
        db.create_all()  # Создаём таблицы
        yield app  # Возвращаем приложение для тестов
        db.session.remove()  # Чистим сессию после тестов
        db.drop_all()  # Удаляем таблицы


def test_create_model_metadata(setup_db):
    with setup_db.app_context():  # Убедитесь, что используете контекст приложения
        # Очистка базы данных перед тестом
        db.session.query(ModelMetadata).delete()
        db.session.commit()

        # Создание тестовой записи
        model = ModelMetadata(
            model_name="Test Model",
            model_version="v1.0",
            number_of_images=1000,
            number_of_classes=10
        )
        db.session.add(model)
        db.session.commit()

        # Проверка данных
        saved_model = ModelMetadata.query.first()
        assert saved_model is not None
        assert saved_model.model_name == "Test Model"
