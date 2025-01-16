import os
import numpy as np
from PIL import Image
from flask import request, send_file, url_for, jsonify
from werkzeug.utils import secure_filename
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv2D, MaxPooling2D
from tensorflow.keras.optimizers import Adam
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

                # Проверяем, существует ли метка в class_names
                if actual_label not in class_names:
                    return jsonify(success=False, error="Неверная метка класса")

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

    @app.route('/train_model', methods=['POST'])
    def train_and_download_model():
        try:
            # Загружаем изображения из базы данных
            image_data, labels = load_images_from_db()

            # Обучаем модель
            model_path = train_model(image_data, labels)

            # После обучения, отправляем модель для скачивания
            return jsonify(success=True, message="Модель обучена. Вы можете скачать её.",
                           download_url=url_for('download_model'))

        except Exception as e:
            # Логируем ошибку на сервере для дальнейшего анализа
            app.logger.error(f"Ошибка при обучении модели: {str(e)}")

            # Возвращаем ошибку пользователю
            return jsonify(success=False, error=f"Произошла ошибка при обучении модели: {str(e)}")

    @app.route('/download_model', methods=['GET'])
    def download_model():
        try:
            # Указываем путь к модели
            model_path = os.path.join('app', 'static', 'models', 'cifar10_model.h5')

            # Проверяем, существует ли файл
            if not os.path.exists(model_path):
                print(f"File not found: {model_path}")
                return jsonify({"error": "Model file not found."}), 404

            print(f"Serving file: {model_path}")
            # Отправляем файл клиенту
            return send_file(model_path, as_attachment=True)
        except Exception as e:
            print(f"Error occurred: {e}")
            return jsonify({"error": str(e)}), 500


def load_images_from_db():
    # Извлекаем все изображения из базы данных
    images = ImageModel.query.all()

    # Список для изображений и меток
    image_data = []
    labels = []

    # Загружаем каждое изображение и добавляем его в список
    for img in images:
        # Получаем полный путь к изображению
        img_path = os.path.join(os.getcwd(), 'app', 'static', img.image_path.split('/')[-1])

        # Открываем изображение
        img_array = image.load_img(img_path, target_size=(32, 32))  # CIFAR-10 имеет размер 32x32
        img_array = image.img_to_array(img_array) / 255.0  # Нормализуем пиксели в диапазон [0, 1]

        # Преобразуем строковую метку в числовую
        if img.actual_label.isdigit():  # Если метка числовая
            label_index = int(img.actual_label)  # Используем её как индекс
        else:
            label_index = class_names.index(img.actual_label)  # Ищем строковую метку в class_names

        image_data.append(img_array)
        labels.append(label_index)

    return np.array(image_data), np.array(labels)


def train_model(image_data, labels):
    # Создаем простую сверточную нейронную сеть
    model = Sequential()

    model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Flatten())
    model.add(Dense(64, activation='relu'))
    model.add(Dense(10, activation='softmax'))  # 10 классов для CIFAR-10

    # Компилируем модель
    model.compile(optimizer=Adam(), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    # Обучаем модель
    model.fit(image_data, labels, epochs=10, batch_size=32)

    # Сохраняем модель
    model.save('cifar10_model.h5')

    # Убедитесь, что папка static/models существует
    os.makedirs(os.path.join('app', 'static', 'models'), exist_ok=True)

    # Сохраняем модель
    model_path = os.path.join('app', 'static', 'models', 'cifar10_model.h5')
    model.save(model_path)

    return model_path  # Возвращаем путь к модели
