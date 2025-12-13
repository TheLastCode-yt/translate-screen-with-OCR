
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QFormLayout, QMessageBox, QColorDialog, QSpinBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal
from ui.styles import STYLES

class SettingsWindow(QWidget):
    settings_saved = pyqtSignal()
    request_define_crop = pyqtSignal()

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        self.setStyleSheet(STYLES)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        # API Keys
        self.deepl_key = QLineEdit(self.config.get_api_key("deepl"))
        self.google_key = QLineEdit(self.config.get_api_key("google"))
        self.google_key.setPlaceholderText("Optional (for Cloud API)")
        
        form.addRow("DeepL API Key:", self.deepl_key)
        form.addRow("Google API Key:", self.google_key)

        # Languages
        languages = ["pt", "es", "en", "zh", "ja", "ko", "fr", "de", "it", "ru"]
        
        # Source Language
        self.source_lang = QComboBox()
        self.source_lang.addItems(languages)
        self.source_lang.setCurrentText(self.config.get("source_language", "en"))
        form.addRow("Source Language:", self.source_lang)

        # Target Language
        self.target_lang = QComboBox()
        self.target_lang.addItems(languages)
        self.target_lang.setCurrentText(self.config.get("target_language", "pt"))
        form.addRow("Target Language:", self.target_lang)

        # Default Capture Mode
        self.capture_mode = QComboBox()
        self.capture_mode.addItems(["global", "crop"])
        self.capture_mode.setCurrentText(self.config.get("default_capture_mode", "global"))
        form.addRow("Default Capture Mode:", self.capture_mode)
        
        # Define Crop Button (Only visible if crop is selected, or always visible but enabled/disabled?)
        # User said "when the person define the capture mode as crop we put a button right below written define crop"
        self.btn_define_crop = QPushButton("Define Crop")
        self.btn_define_crop.clicked.connect(self.request_define_crop.emit)
        form.addRow("", self.btn_define_crop) # Empty label for alignment
        
        # Logic to show/hide or enable/disable based on selection
        self.capture_mode.currentTextChanged.connect(self.toggle_crop_button)
        self.toggle_crop_button(self.capture_mode.currentText())

        # Default Provider
        self.provider = QComboBox()
        self.provider.addItems(["mymemory", "google", "deepl"])
        self.provider.setCurrentText(self.config.get("default_provider", "mymemory"))
        form.addRow("Translation Provider:", self.provider)

        # --- Bubble Appearance ---
        form.addRow(QLabel("<b>Bubble Appearance</b>"))
        
        # Background Color
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(50, 25)
        self.bg_color = self.config.get("bubble_style", {}).get("background_color", "#2d2d2d")
        self.bg_color_btn.setStyleSheet(f"background-color: {self.bg_color}; border: 1px solid #555;")
        self.bg_color_btn.clicked.connect(lambda: self.pick_color("background_color"))
        form.addRow("Background Color:", self.bg_color_btn)
        
        # Text Color
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(50, 25)
        self.text_color = self.config.get("bubble_style", {}).get("text_color", "#ffffff")
        self.text_color_btn.setStyleSheet(f"background-color: {self.text_color}; border: 1px solid #555;")
        self.text_color_btn.clicked.connect(lambda: self.pick_color("text_color"))
        form.addRow("Text Color:", self.text_color_btn)
        
        # Font Size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 100)
        self.font_size_spin.setValue(self.config.get("bubble_style", {}).get("font_size", 12))
        form.addRow("Font Size:", self.font_size_spin)

        # API Keys Section
        form.addRow(QLabel("<b>API Keys (Optional)</b>"))
        
        self.deepl_key = QLineEdit(self.config.get_api_key("deepl"))
        self.deepl_key.setPlaceholderText("DeepL API Key")
        form.addRow("DeepL Key:", self.deepl_key)
        
        self.google_key = QLineEdit(self.config.get_api_key("google"))
        self.google_key.setPlaceholderText("Google Cloud API Key")
        form.addRow("Google Key:", self.google_key)
        
        # Save Button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addLayout(form)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def pick_color(self, key):
        current = self.bg_color if key == "background_color" else self.text_color
        color = QColorDialog.getColor(QColor(current), self, "Select Color")
        if color.isValid():
            hex_color = color.name()
            if key == "background_color":
                self.bg_color = hex_color
                self.bg_color_btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #555;")
            else:
                self.text_color = hex_color
                self.text_color_btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #555;")

    def toggle_crop_button(self, text):
        self.btn_define_crop.setVisible(text == "crop")

    def save_settings(self):
        self.config.set_api_key("deepl", self.deepl_key.text())
        self.config.set_api_key("google", self.google_key.text())
        
        self.config.set("source_language", self.source_lang.currentText())
        self.config.set("target_language", self.target_lang.currentText())
        self.config.set("default_capture_mode", self.capture_mode.currentText())
        self.config.set("default_provider", self.provider.currentText())
        
        # Save Bubble Style
        bubble_style = {
            "background_color": self.bg_color,
            "text_color": self.text_color,
            "font_size": self.font_size_spin.value()
        }
        self.config.set("bubble_style", bubble_style)
        
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.settings_saved.emit()
        self.close()
