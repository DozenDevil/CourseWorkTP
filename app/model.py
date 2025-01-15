from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ImageModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200), nullable=False)
    actual_label = db.Column(db.String(50), nullable=False)
    predicted_label = db.Column(db.String(50), nullable=True)  # Пока пусто

    def __repr__(self):
        return f'<Image {self.id} - {self.actual_label}>'
