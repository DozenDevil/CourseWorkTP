class ImageModel:
    def __init__(self):
        # Простой список в памяти (замените на базу данных, если нужно)
        self.images = []

    def add_image(self, image_path, label):
        self.images.append({'path': image_path, 'label': label})

    def get_all_images(self):
        return self.images
