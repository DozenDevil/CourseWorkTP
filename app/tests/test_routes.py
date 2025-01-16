import pytest
from app import create_app, db


@pytest.fixture(scope='module')
def setup_app():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()  # Создаём таблицы
        yield app.test_client()  # Возвращаем тестовый клиент
        db.session.remove()
        db.drop_all()  # Удаляем таблицы после тестов


def test_export_metadata_csv(setup_app):
    # Добавляем тестовые данные в базу
    from app.model import ModelMetadata

    with setup_app.application.app_context():
        metadata = ModelMetadata(
            model_name="Test Model",
            model_version="v1.0",
            number_of_images=1000,
            number_of_classes=10
        )
        db.session.add(metadata)
        db.session.commit()

    # Отправляем GET-запрос к маршруту
    response = setup_app.get('/export_metadata?format=csv')

    # Проверяем успешный статус
    assert response.status_code == 200

    # Проверяем JSON-ответ
    data = response.get_json()
    assert data["success"] is True
    assert "/download/model_metadata.csv" in data["download_url"]
