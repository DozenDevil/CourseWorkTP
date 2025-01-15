import os
import numpy as np
from PIL import Image
from flask import request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from tensorflow.keras.datasets import cifar10
from .model import ImageModel, db
from .view import render_template

# Папка для хранения изображений
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Загружаем классы CIFAR-10
class_names = [
    'airplane', 'automobile', 'bird', 'cat', 'deer',
    'dog', 'frog', 'horse', 'ship', 'truck'
]


# Проверка разрешенных форматов изображений
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_routes(app):
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Главная страница (View)
    @app.route('/')
    def index():
        images = ImageModel.get_all_images()  # Получаем все изображения из базы данных
        return render_template('index.html', images=images)

    # Обработчик загрузки изображения
    @app.route('/upload_image', methods=['POST'])
    def upload_image():
        try:
            if 'image' not in request.files:
                return jsonify(success=False, error="Нет файла для загрузки.")

            images = request.files.getlist('image')  # Получаем список файлов
            uploaded_images = []

            for img in images:
                if img.filename == '':
                    continue

                # Проверяем тип файла
                if not img.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    return jsonify(success=False, error="Только изображения форматов PNG, JPG и JPEG разрешены.")

                # Определяем имя файла
                filename = img.filename
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Сохраняем изображение
                img.save(image_path)

                # Извлекаем класс из имени файла
                actual_label = filename.split('_')[0]  # Предполагаем, что метка класса в имени файла
                if actual_label.isdigit():
                    actual_label = class_names[int(actual_label)]

                # Добавляем изображение в базу данных
                new_image = ImageModel(image_path=image_path, actual_label=actual_label)
                db.session.add(new_image)

                uploaded_images.append(new_image)

            # Завершаем запись в базу данных
            db.session.commit()

            # Отправляем обратно информацию о загруженных изображениях
            images_data = [{
                'image_path': image.image_path,
                'actual_label': image.actual_label,
                'predicted_label': image.predicted_label or 'Не классифицировано'
            } for image in uploaded_images]

            return jsonify(success=True, images=images_data)

        except Exception as e:
            return jsonify(success=False, error=str(e))

    @app.route('/load_cifar10')
    def load_cifar10():
        try:
            # Загружаем CIFAR-10
            (x_train, y_train), (_, _) = cifar10.load_data()

            # Ограничиваемся первыми 100 изображениями
            for i, (image_data, label) in enumerate(zip(x_train[:100], y_train[:100])):  # только первые 100 изображений
                # Преобразуем в изображение
                image = Image.fromarray(image_data)
                image_filename = f"cifar10_{i}.png"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)

                # Сохраняем изображение
                image.save(image_path)

                # Сохраняем в базу данных
                new_image = ImageModel(image_path=image_path, actual_label=class_names[label[0]])
                db.session.add(new_image)

                # Каждые 10 изображений - сохраняем в базе, чтобы избежать переполнения
                if i % 10 == 0:
                    db.session.commit()

            # Завершаем запись в базу данных
            db.session.commit()

            return jsonify(success=True)

        except Exception as e:
            # В случае ошибки
            return jsonify(success=False, error=str(e))
