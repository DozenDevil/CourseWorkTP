from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ImageModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200), nullable=False)
    actual_label = db.Column(db.String(50), nullable=False)
    predicted_label = db.Column(db.String(50), nullable=True)  # Пока пусто

    def __repr__(self):
        return f'<Image {self.id} - {self.actual_label}>'

    @classmethod
    def save_image(cls, image_path, actual_label):
        new_image = cls(image_path=image_path, actual_label=actual_label)
        db.session.add(new_image)
        db.session.commit()

    @classmethod
    def get_all_images(cls):
        return cls.query.all()
