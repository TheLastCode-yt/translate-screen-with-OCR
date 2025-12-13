from PyQt6.QtWidgets import QWidget, QLabel, QApplication, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint, QSize, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QCursor

class SelectionControl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.btn_save = QPushButton("✓")
        self.btn_save.setFixedSize(30, 30)
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        
        self.btn_cancel = QPushButton("✕")
        self.btn_cancel.setFixedSize(30, 30)
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_cancel)
        self.setLayout(layout)

class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(50)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        
        pen = QPen(QColor("#3498db"), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw arc
        painter.drawArc(-12, -12, 24, 24, 0 * 16, 270 * 16)

class TranslationBubble(QWidget):
    def __init__(self, text, x, y, w, h, parent=None, config=None):
        super().__init__(parent)
        self.text = text
        self.target_rect = QRect(x, y, w, h)
        self.config = config
        
        # Default styles
        self.bg_color = QColor("#2d2d2d")
        self.text_color = QColor("#ffffff")
        self.font_size = 12
        
        # Load from config if available
        if self.config:
            style = self.config.get("bubble_style", {})
            self.bg_color = QColor(style.get("background_color", "#2d2d2d"))
            self.text_color = QColor(style.get("text_color", "#ffffff"))
            self.font_size = style.get("font_size", 12)
        
        self.init_ui()
        self.show()

    def init_ui(self):
        # ... (rest of init_ui logic, but using self.bg_color, self.text_color, self.font_size)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        
        # Apply styles
        self.label.setStyleSheet(f"color: {self.text_color.name()}; font-size: {self.font_size}px; font-family: 'Segoe UI', sans-serif;")
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # Adjust size based on content
        self.adjustSize()
        
        # Position: Try to place at top-left of target_rect
        # But ensure it's on screen
        self.move(self.target_rect.topLeft())
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw bubble background
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

class OverlayWindow(QWidget):
    on_selection_complete = pyqtSignal(QRect)
    on_dismiss = pyqtSignal()

    def __init__(self, config=None): # Accept config
        super().__init__()
        self.config = config
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        self.mode = "SELECT" # SELECT, EDIT, DISPLAY
        self.selection_rect = QRect()
        self.is_drawing = False
        self.active_handle = None # 'tl', 'tr', 'bl', 'br', 'move', None
        self.drag_start_pos = QPoint()
        self.rect_start_geo = QRect()
        
        self.bubbles = []
        
        # Controls
        self.controls = SelectionControl(self)
        self.controls.hide()
        self.controls.btn_save.clicked.connect(self.confirm_selection)
        self.controls.btn_cancel.clicked.connect(self.cancel_selection)
        
        # Loading
        self.loading_spinner = LoadingSpinner(self)
        self.loading_spinner.hide()

    def show_loading(self, rect=None):
        self.loading_spinner.show()
        self.loading_spinner.raise_()
        
        if rect:
            # Center in rect
            x = rect.center().x() - self.loading_spinner.width() // 2
            y = rect.center().y() - self.loading_spinner.height() // 2
            self.loading_spinner.move(x, y)
        else:
            # Center on screen
            x = self.width() // 2 - self.loading_spinner.width() // 2
            y = self.height() // 2 - self.loading_spinner.height() // 2
            self.loading_spinner.move(x, y)
            
    def hide_loading(self):
        self.loading_spinner.hide()

    def set_mode(self, mode):
        self.mode = mode
        self.selection_rect = QRect()
        self.controls.hide()
        self.clear_bubbles()
        self.hide_loading() # Hide loading when changing mode
        
        if mode == "DISPLAY":
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)
        self.update()

    def clear_bubbles(self):
        for bubble in self.bubbles:
            bubble.close()
        self.bubbles = []

    def set_initial_rect(self, rect):
        if rect:
            self.selection_rect = rect
            self.mode = "EDIT"
            self.update_controls_pos()
            self.controls.show()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

    def add_bubble(self, text, x, y, w, h):
        # x, y are global coordinates. Convert to local.
        local_pos = self.mapFromGlobal(QPoint(x, y))
        bubble = TranslationBubble(text, local_pos.x(), local_pos.y(), w, h, self, self.config)
        bubble.show()
        self.bubbles.append(bubble)

    def confirm_selection(self):
        if self.selection_rect.isValid() and not self.selection_rect.isEmpty():
            self.on_selection_complete.emit(self.selection_rect)
            self.controls.hide()

    def cancel_selection(self):
        self.selection_rect = QRect()
        self.controls.hide()
        self.mode = "SELECT"
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.update()

    def get_handles(self):
        r = self.selection_rect
        s = 10 # Handle size
        return {
            'tl': QRect(r.left() - s//2, r.top() - s//2, s, s),
            'tr': QRect(r.right() - s//2, r.top() - s//2, s, s),
            'bl': QRect(r.left() - s//2, r.bottom() - s//2, s, s),
            'br': QRect(r.right() - s//2, r.bottom() - s//2, s, s)
        }

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if (self.mode == "SELECT" or self.mode == "EDIT") and not self.selection_rect.isEmpty():
            # Clear rect area
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.selection_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # Draw border
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.selection_rect)
            
            # Draw handles if in EDIT mode
            if self.mode == "EDIT":
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                for handle in self.get_handles().values():
                    painter.drawRect(handle)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = event.pos()

        if self.mode == "EDIT":
            # Check handles
            handles = self.get_handles()
            for name, rect in handles.items():
                if rect.contains(pos):
                    self.active_handle = name
                    self.drag_start_pos = pos
                    self.rect_start_geo = self.selection_rect
                    return

            # Check move
            if self.selection_rect.contains(pos):
                self.active_handle = 'move'
                self.drag_start_pos = pos
                self.rect_start_geo = self.selection_rect
                return
            
            # Click outside -> New selection
            self.mode = "SELECT"
            self.selection_rect = QRect()
            self.controls.hide()
            self.update()

        if self.mode == "SELECT":
            self.is_drawing = True
            self.drag_start_pos = pos
            self.selection_rect = QRect(pos, QSize(0, 0))
            self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()

        if self.mode == "EDIT" and not self.active_handle:
            # Update cursor
            handles = self.get_handles()
            cursor = Qt.CursorShape.ArrowCursor
            if handles['tl'].contains(pos) or handles['br'].contains(pos):
                cursor = Qt.CursorShape.SizeFDiagCursor
            elif handles['tr'].contains(pos) or handles['bl'].contains(pos):
                cursor = Qt.CursorShape.SizeBDiagCursor
            elif self.selection_rect.contains(pos):
                cursor = Qt.CursorShape.SizeAllCursor
            self.setCursor(cursor)

        if self.active_handle:
            delta = pos - self.drag_start_pos
            r = self.rect_start_geo
            
            if self.active_handle == 'move':
                self.selection_rect.moveTo(r.topLeft() + delta)
            elif self.active_handle == 'tl':
                self.selection_rect.setTopLeft(r.topLeft() + delta)
            elif self.active_handle == 'tr':
                self.selection_rect.setTopRight(r.topRight() + delta)
            elif self.active_handle == 'bl':
                self.selection_rect.setBottomLeft(r.bottomLeft() + delta)
            elif self.active_handle == 'br':
                self.selection_rect.setBottomRight(r.bottomRight() + delta)
            
            self.selection_rect = self.selection_rect.normalized()
            self.update_controls_pos()
            self.update()

        elif self.is_drawing:
            self.selection_rect = QRect(self.drag_start_pos, pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_drawing:
            self.is_drawing = False
            if self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
                self.mode = "EDIT"
                self.update_controls_pos()
                self.controls.show()
                self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.selection_rect = QRect()
                self.update()
        
        self.active_handle = None

    def update_controls_pos(self):
        # Position controls to the right of the rect, centered vertically
        r = self.selection_rect
        cw = self.controls.width()
        ch = self.controls.height()
        
        x = r.right() + 10
        y = r.center().y() - ch // 2
        
        # Keep on screen
        if x + cw > self.width():
            # If not enough space on right, put on left
            x = r.left() - cw - 10
        
        if y < 0: y = 0
        if y + ch > self.height(): y = self.height() - ch
        
        self.controls.move(x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.on_dismiss.emit()
            self.close()
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            if self.mode == "EDIT":
                self.confirm_selection()
