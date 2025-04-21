# src/ui_main.py
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QScrollArea, QFrame, QMessageBox, QLineEdit
)
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, QDate


from ui_add_product import AddProductDialog
from db import get_connection
from models import Product

CATEGORIES = ["All", "Skincare", "Makeup", "Haircare", "Fragrance", "Nails", "Tools", "Bath & Body"]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cosmetic Stock Manager")
        self.setGeometry(100, 100, 1000, 600)
        

        # Load style
        with open(os.path.join("styles", "theme.qss"), "r") as f:
            self.setStyleSheet(f.read())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        

        self.category_list = QListWidget()
        for cat in CATEGORIES:
            self.category_list.addItem(cat)
        self.category_list.itemClicked.connect(self.filter_by_category)
        self.layout.addWidget(self.category_list, 1)

        self.main_content = QVBoxLayout()
        self.layout.addLayout(self.main_content, 4)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products...")
        self.search_input.textChanged.connect(self.search_products)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 2px solid #E0B0FF;
                border-radius: 10px;
                background-color: #fff0f9;
                font-size: 14px;
            }
        """)
        self.main_content.addWidget(self.search_input)



        self.header = QHBoxLayout()
        self.title = QLabel("📦 Cosmetic Product Stock")
        self.title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.header.addWidget(self.title)

        self.add_button = QPushButton("➕ Add Product")
        self.add_button.clicked.connect(self.open_add_product)
        self.header.addWidget(self.add_button)

        self.main_content.addLayout(self.header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.products_container = QWidget()
        self.products_layout = QVBoxLayout()
        self.products_container.setLayout(self.products_layout)
        self.scroll.setWidget(self.products_container)
        self.main_content.addWidget(self.scroll)

        self.load_products()
    
    def search_products(self, text):
        text = text.lower()
        for i in range(self.products_layout.count()):
            widget = self.products_layout.itemAt(i).widget()
            if widget:
                match = False
                for label in widget.findChildren(QLabel):
                    if text in label.text().lower():
                        match = True
                        break
                widget.setVisible(match)

    def load_products(self, category="All"):
        # Clear previous items
        for i in reversed(range(self.products_layout.count())):
            widget = self.products_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        conn = get_connection()
        cursor = conn.cursor()

        if category == "All":
            cursor.execute("SELECT * FROM products")
        else:
            cursor.execute("SELECT * FROM products WHERE category=?", (category,))

        for row in cursor.fetchall():
            product_widget = self.create_product_card(*row)
            self.products_layout.addWidget(product_widget)

        conn.close()
        self.highlight_expirations()

    def highlight_expirations(self):
        today = QDate.currentDate()
        warning_date = today.addDays(30)

        for i in range(self.products_layout.count()):
            card = self.products_layout.itemAt(i).widget()
            if card:
                labels = card.findChildren(QLabel)
                for label in labels:
                    if label.text().startswith("Expires:"):
                        expiration_text = label.text().replace("Expires:", "").strip()
                        expiration_date = QDate.fromString(expiration_text, "yyyy-MM-dd")
                        if expiration_date.isValid():
                            if expiration_date < today:
                                label.setStyleSheet("color: white; background-color: red; padding: 2px 4px; border-radius: 4px;")
                            elif expiration_date <= warning_date:
                                label.setStyleSheet("color: black; background-color: yellow; padding: 2px 4px; border-radius: 4px;")
                            else:
                                label.setStyleSheet("")



    def create_product_card(self, id, code, name, description, expiration, image_path, category):
        card = QFrame()
        card.setStyleSheet("background-color: white; border: 1px solid #eee; border-radius: 12px; padding: 10px;")
        layout = QHBoxLayout()
        card.setLayout(layout)

        image = QLabel()
        pixmap = QPixmap(image_path)
        image.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(image)

        info = QVBoxLayout()
        info.addWidget(QLabel(f"<b>{name}</b>"))
        info.addWidget(QLabel(f"Code: {code}"))
        info.addWidget(QLabel(f"Category: {category}"))
        info.addWidget(QLabel(f"Expires: {expiration}"))
        info.addWidget(QLabel(f"{description}"))
        layout.addLayout(info)
        # Add at the bottom of create_product_card in ui_main.py

        # Add action buttons
        button_layout = QVBoxLayout()
        edit_btn = QPushButton("✏️ Edit")
        delete_btn = QPushButton("🗑 Delete")

        edit_btn.clicked.connect(lambda: self.edit_product(id))
        delete_btn.clicked.connect(lambda: self.delete_product(id))

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)
        return card

    def open_add_product(self):
        dialog = AddProductDialog()
        if dialog.exec():
            self.load_products()

    def filter_by_category(self, item: QListWidgetItem):
        self.load_products(item.text())
    
    def edit_product(self, product_id):
        from ui_add_product import EditProductDialog
        dialog = EditProductDialog(product_id)
        if dialog.exec():
            self.load_products()

    def delete_product(self, product_id):
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this product?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Deleted", "Product has been deleted.")
            self.load_products()
    
    

