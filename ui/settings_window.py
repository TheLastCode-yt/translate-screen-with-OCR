from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QFormLayout, QMessageBox)
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
        self.provider.addItems(["mymemory", "deepl", "google"])
        self.provider.setCurrentText(self.config.get("default_provider", "mymemory"))
        form.addRow("Default Provider:", self.provider)

        layout.addLayout(form)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def toggle_crop_button(self, text):
        self.btn_define_crop.setVisible(text == "crop")

    def save_settings(self):
        self.config.set_api_key("deepl", self.deepl_key.text())
        self.config.set_api_key("google", self.google_key.text())
        self.config.set("source_language", self.source_lang.currentText())
        self.config.set("target_language", self.target_lang.currentText())
        self.config.set("default_capture_mode", self.capture_mode.currentText())
        self.config.set("default_provider", self.provider.currentText())
        
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.settings_saved.emit()
        self.close()
