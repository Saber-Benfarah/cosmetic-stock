# src/ui_add_product.py
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QDateEdit, QFileDialog, QComboBox, QMessageBox
)
from PySide6.QtCore import QDate
from db import get_connection
from datetime import datetime
import shutil

CATEGORIES = ["Skincare", "Makeup", "Haircare", "Fragrance", "Nails", "Tools", "Bath & Body"]
ASSETS_FOLDER = os.path.join(os.path.dirname(__file__), "../assets/products")

class AddProductDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Product")
        self.setMinimumWidth(400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Product Code")
        self.layout.addWidget(self.code_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")
        self.layout.addWidget(self.name_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Product Description")
        self.layout.addWidget(self.description_input)

        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDate(QDate.currentDate())
        self.layout.addWidget(self.expiry_input)

        self.category_input = QComboBox()
        self.category_input.addItems(CATEGORIES)
        self.layout.addWidget(self.category_input)

        self.image_path = ""
        self.image_button = QPushButton("Upload Image")
        self.image_button.clicked.connect(self.upload_image)
        self.layout.addWidget(self.image_button)

        self.save_button = QPushButton("Save Product")
        self.save_button.clicked.connect(self.save_product)
        self.layout.addWidget(self.save_button)

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Product Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            self.image_path = file_path
            self.image_button.setText("Image Selected ✔")

    def save_product(self):
        code = self.code_input.text()
        name = self.name_input.text()
        description = self.description_input.toPlainText()
        expiration = self.expiry_input.date().toString("yyyy-MM-dd")
        category = self.category_input.currentText()

        if not all([code, name, description, self.image_path]):
            QMessageBox.warning(self, "Missing Fields", "Please fill in all fields and select an image.")
            return

        # Save image to assets/products
        if not os.path.exists(ASSETS_FOLDER):
            os.makedirs(ASSETS_FOLDER)
        filename = f"{code}_{os.path.basename(self.image_path)}"
        dest_path = os.path.join(ASSETS_FOLDER, filename)
        shutil.copy(self.image_path, dest_path)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO products (code, name, description, expiration_date, image_path, category)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (code, name, description, expiration, dest_path, category))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Product added successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save product.\n{str(e)}")
class EditProductDialog(AddProductDialog):
    def __init__(self, product_id):
        super().__init__()
        self.setWindowTitle("Edit Product")
        self.product_id = product_id
        self.load_existing_product()

    def load_existing_product(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id=?", (self.product_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            self.code_input.setText(row[1])
            self.name_input.setText(row[2])
            self.description_input.setPlainText(row[3])
            date = QDate.fromString(row[4], "yyyy-MM-dd")
            self.expiry_input.setDate(date)
            self.image_path = row[5]
            self.category_input.setCurrentText(row[6])
            self.image_button.setText("Image Selected ✔")

    def save_product(self):
        code = self.code_input.text()
        name = self.name_input.text()
        description = self.description_input.toPlainText()
        expiration = self.expiry_input.date().toString("yyyy-MM-dd")
        category = self.category_input.currentText()

        if not all([code, name, description]):
            QMessageBox.warning(self, "Missing Fields", "Please fill in all fields.")
            return

        if self.image_path and not os.path.exists(self.image_path):
            filename = f"{code}_{os.path.basename(self.image_path)}"
            dest_path = os.path.join(ASSETS_FOLDER, filename)
            shutil.copy(self.image_path, dest_path)
        else:
            dest_path = self.image_path

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE products SET code=?, name=?, description=?, expiration_date=?, image_path=?, category=?
            WHERE id=?
            """, (code, name, description, expiration, dest_path, category, self.product_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Product updated.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update product.\n{str(e)}")
