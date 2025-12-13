from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QPushButton)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QSize, Qt
from ui.styles import STYLES
import io

class LogsWindow(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.setWindowTitle("Translation Logs")
        self.resize(800, 500)
        self.setStyleSheet(STYLES)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Image", "Original", "Translated", "Timestamp"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(3, 150)
        self.table.setIconSize(QSize(80, 80))
        
        layout.addWidget(self.table)
        
        # Clear Logs Button
        self.btn_clear = QPushButton("Clear All Logs")
        self.btn_clear.clicked.connect(self.clear_logs)
        layout.addWidget(self.btn_clear)
        
        self.setLayout(layout)
        
        self.refresh_logs()

    def clear_logs(self):
        self.config.clear_history()
        self.refresh_logs()

    def refresh_logs(self):
        history = self.config.get_history()
        self.table.setRowCount(len(history))
        
        # Show latest first
        for i, entry in enumerate(reversed(history)):
            self.set_row_data(i, entry)

    def add_log(self, original, translated, image_data):
        # Insert new row at top
        self.table.insertRow(0)
        entry = {
            "original": original,
            "translated": translated,
            "image_data": image_data,
            "timestamp": "Just now" # Or pass timestamp
        }
        self.set_row_data(0, entry)

    def set_row_data(self, row, entry):
        # Image
        image_data = entry.get("image_data")
        if image_data:
            try:
                # Convert PIL Image to QPixmap
                # Save to bytes
                byte_array = io.BytesIO()
                image_data.save(byte_array, format="PNG")
                qimage = QPixmap()
                qimage.loadFromData(byte_array.getvalue())
                
                icon = QIcon(qimage)
                item = QTableWidgetItem()
                item.setIcon(icon)
                self.table.setItem(row, 0, item)
            except Exception as e:
                print(f"Error displaying image: {e}")
                self.table.setItem(row, 0, QTableWidgetItem("Error"))
        else:
            self.table.setItem(row, 0, QTableWidgetItem("No Image"))

        self.table.setItem(row, 1, QTableWidgetItem(entry.get("original", "")))
        self.table.setItem(row, 2, QTableWidgetItem(entry.get("translated", "")))
        self.table.setItem(row, 3, QTableWidgetItem(entry.get("timestamp", "")))
        self.table.setRowHeight(row, 80)
