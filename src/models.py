# src/models.py

class Product:
    def __init__(self, code, name, description, expiration_date, image_path, category):
        self.code = code
        self.name = name
        self.description = description
        self.expiration_date = expiration_date
        self.image_path = image_path
        self.category = category
