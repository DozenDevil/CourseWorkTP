from flask_sqlalchemy import SQLAlchemy
from abc import ABC, abstractmethod
import csv
import json
import os
from datetime import datetime

db = SQLAlchemy()


class ImageModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200), nullable=False)
    actual_label = db.Column(db.String(50), nullable=False)
    predicted_label = db.Column(db.String(50), nullable=True)

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


class ModelMetadata(db.Model):
    __tablename__ = 'model_metadata'
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(255), nullable=False)
    model_version = db.Column(db.String(255), nullable=False)
    number_of_images = db.Column(db.Integer, nullable=False)
    number_of_classes = db.Column(db.Integer, nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ModelMetadata(model_name={self.model_name}, model_version={self.model_version})>"


class ExportStrategy(ABC):

    @abstractmethod
    def export(self, metadata):
        pass


class ExportToCSV(ExportStrategy):
    def export(self, metadata, export_folder):
        metadata_list = [{
            'id': entry.id,
            'model_name': entry.model_name,
            'model_version': entry.model_version,
            'number_of_images': entry.number_of_images,
            'number_of_classes': entry.number_of_classes,
            'creation_date': entry.creation_date.strftime('%Y-%m-%d %H:%M:%S')
        } for entry in metadata]

        # Путь для сохранения файла
        filename = "model_metadata.csv"
        file_path = os.path.join(export_folder, filename)

        with open(file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=metadata_list[0].keys())
            writer.writeheader()
            writer.writerows(metadata_list)

        return filename  # Возвращаем название файла для скачивания


class ExportToJSON(ExportStrategy):
    def export(self, metadata, export_folder):
        metadata_list = [{
            'id': entry.id,
            'model_name': entry.model_name,
            'model_version': entry.model_version,
            'number_of_images': entry.number_of_images,
            'number_of_classes': entry.number_of_classes,
            'creation_date': entry.creation_date.strftime('%Y-%m-%d %H:%M:%S')
        } for entry in metadata]

        # Путь для сохранения файла
        filename = "model_metadata.json"
        file_path = os.path.join(export_folder, filename)

        with open(file_path, 'w') as json_file:
            json.dump(metadata_list, json_file, indent=4)

        return filename  # Возвращаем название файла для скачивания
