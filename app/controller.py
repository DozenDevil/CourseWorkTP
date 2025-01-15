from flask import request, redirect, url_for, flash
from .model import ImageModel
from .view import render_index

# Инициализация модели
image_model = ImageModel()

def init_routes(app):
    @app.route('/')
    def index():
        images = image_model.get_all_images()
        return render_index(images)

    @app.route('/add_image', methods=['POST'])
    def add_image():
        image_path = request.form.get('image_path')
        label = request.form.get('label')

        if not image_path or not label:
            flash("Укажите путь к изображению и класс!")
            return redirect(url_for('index'))

        image_model.add_image(image_path, label)
        flash(f"Изображение '{image_path}' с классом '{label}' добавлено!")
        return redirect(url_for('index'))
