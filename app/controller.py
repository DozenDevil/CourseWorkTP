import os
import numpy as np
from PIL import Image
from flask import request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from tensorflow.keras.datasets import cifar10
from .model import ImageModel, db
from .view import render_index

# Папка для хранения изображений
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Проверка разрешенных форматов изображений
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_routes(app):
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.route('/')
    def index():
        images = ImageModel.query.all()  # Получаем все изображения из базы данных
        return render_index(images)

    # Обработчик для загрузки изображения
    @app.route('/upload', methods=['POST'])
    def upload_image():
        if 'image' not in request.files:
            return "No file part", 400
        file = request.files['image']
        if file.filename == '':
            return "No selected file", 400
        if file and allowed_file(file.filename):
            # Сохраняем файл с безопасным именем
            filename = secure_filename(file.filename)
            # Извлекаем класс из имени файла
            class_name = filename.split('_')[0]  # Извлекаем номер класса
            class_number = int(class_name)  # Преобразуем в целое число
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return f"File uploaded successfully with class {class_number}", 200
        return "Invalid file format", 400

    @app.route('/load_cifar10')
    def load_cifar10():
        try:
            # Загружаем CIFAR-10
            (x_train, y_train), (_, _) = cifar10.load_data()

            # Загружаем классы CIFAR-10
            class_names = [
                'airplane', 'automobile', 'bird', 'cat', 'deer',
                'dog', 'frog', 'horse', 'ship', 'truck'
            ]

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
