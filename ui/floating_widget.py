from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QApplication, 
                             QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QSize, QRect, QEvent
from PyQt6.QtGui import QCursor, QIcon, QAction
from ui.styles import STYLES

class FloatingWidget(QWidget):
    request_settings = pyqtSignal()
    request_logs = pyqtSignal()
    request_translate = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("FloatingWidget")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.is_expanded = False
        self.old_pos = None
        self.start_pos = None
        
        self.init_ui()

    def init_ui(self):
        self.resize(60, 60) # Initial size
        
        # Main Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Main Button (The Icon)
        self.main_btn = QPushButton("文")
        self.main_btn.setFixedSize(60, 60)
        self.main_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.main_btn.clicked.connect(self.toggle_menu)
        self.main_btn.installEventFilter(self)
        self.main_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: #4CAF50;
                border-radius: 30px;
                border: 2px solid #4CAF50;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
            }
        """)
        
        # Container for sub-buttons
        self.sub_menu_container = QWidget()
        self.sub_menu_layout = QVBoxLayout(self.sub_menu_container)
        self.sub_menu_layout.setContentsMargins(0, 0, 0, 0)
        self.sub_menu_layout.setSpacing(5)
        
        # Sub-buttons
        self.btn_translate = self.create_sub_button("Translate", self.request_translate)
        self.btn_settings = self.create_sub_button("Settings", self.request_settings)
        self.btn_logs = self.create_sub_button("Logs", self.request_logs)
        self.btn_quit = self.create_sub_button("Quit", QApplication.instance().quit)
        
        self.sub_menu_layout.addWidget(self.btn_translate)
        self.sub_menu_layout.addWidget(self.btn_settings)
        self.sub_menu_layout.addWidget(self.btn_logs)
        self.sub_menu_layout.addWidget(self.btn_quit)
        
        # Hide sub-menu initially
        self.sub_menu_container.hide()
        
        self.layout.addWidget(self.main_btn)
        self.layout.addWidget(self.sub_menu_container)
        
        self.setLayout(self.layout)

    def create_sub_button(self, text, signal_or_slot):
        btn = QPushButton(text)
        btn.setFixedSize(100, 35)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #FFF;
                border: 1px solid #555;
                border-radius: 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #444;
                border-color: #4CAF50;
            }
        """)
        if isinstance(signal_or_slot, pyqtSignal):
            btn.clicked.connect(signal_or_slot.emit)
        else:
            btn.clicked.connect(signal_or_slot)
        return btn

    def toggle_menu(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self.is_expanded = True
        self.sub_menu_container.show()
        
        # Animate Height
        # We need to resize the window to fit content
        content_height = 60 + 5 + (4 * 40) + 10 # Approx height
        self.resize(120, content_height)
        
        # Animation for sub-menu container (fade in or slide)
        # For simplicity, just show it. 
        # To animate window resize is tricky with frameless.
        # Let's just resize.
        
    def collapse(self):
        self.is_expanded = False
        self.sub_menu_container.hide()
        self.resize(60, 60)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Only allow drag if clicking the main button area (top)
            # But since main_btn consumes its own click, we might need to handle this carefully.
            # Actually, if we click the widget background, we can drag.
            # But the widget is mostly buttons.
            # Let's allow dragging by clicking anywhere that is not a button?
            # Or better: install event filter on main button to handle drag?
            # For now, let's assume user drags by clicking the main button (if we pass event)
            # But QPushButton consumes mouse events.
            
            # Alternative: Add a small drag handle or allow dragging from the main button if held?
            # Easier: Implement drag on the main button itself by subclassing or event filter.
            pass
        
        # We'll implement drag in the main button's event filter or subclass
        # But wait, self.main_btn is a child.
        
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def eventFilter(self, source, event):
        if source == self.main_btn:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.old_pos = event.globalPosition().toPoint()
                    self.start_pos = event.globalPosition().toPoint() # Track start to check distance
                    return False # Let button handle press for visual feedback
            
            elif event.type() == QEvent.Type.MouseMove:
                if self.old_pos:
                    delta = event.globalPosition().toPoint() - self.old_pos
                    self.move(self.x() + delta.x(), self.y() + delta.y())
                    self.old_pos = event.globalPosition().toPoint()
                    return True # Consume move event so button doesn't get confused
            
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self.old_pos:
                    # Check if moved significantly
                    if self.start_pos:
                        moved_dist = (event.globalPosition().toPoint() - self.start_pos).manhattanLength()
                        self.old_pos = None
                        self.start_pos = None
                        if moved_dist > 5:
                            return True # It was a drag, consume event (don't click)
                    self.old_pos = None
                    
        return super().eventFilter(source, event)

