from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QApplication,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)
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
        self.btn_save.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #45a049; }
        """
        )

        self.btn_cancel = QPushButton("✕")
        self.btn_cancel.setFixedSize(30, 30)
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """
        )

        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_cancel)
        self.setLayout(layout)


class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)  # Increased size from 40x40 to 100x100
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(16)  # ~60 FPS for smoother animation (reduced from 50ms)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def rotate(self):
        self.angle = (self.angle + 6) % 360  # Smaller increment for smoother rotation
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)

        # Rainbow gradient: yellow -> orange -> red
        pen_width = 8  # Thicker line for bigger spinner

        # Draw multiple arcs with different colors for rainbow effect
        # Yellow arc (0-90 degrees)
        pen_yellow = QPen(QColor("#FFD700"), pen_width)
        pen_yellow.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_yellow)
        painter.drawArc(-30, -30, 60, 60, 0 * 16, 90 * 16)

        # Orange arc (90-180 degrees)
        pen_orange = QPen(QColor("#FF8C00"), pen_width)
        pen_orange.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_orange)
        painter.drawArc(-30, -30, 60, 60, 90 * 16, 90 * 16)

        # Red arc (180-270 degrees)
        pen_red = QPen(QColor("#FF0000"), pen_width)
        pen_red.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_red)
        painter.drawArc(-30, -30, 60, 60, 180 * 16, 90 * 16)


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

        # Window flags for bubble
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.init_ui()
        self.show()

    def keyPressEvent(self, event):
        """Handle ESC key to close the bubble and potentially the overlay."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            # If parent is OverlayWindow, try to close it too or trigger dismiss
            if self.parent():
                try:
                    if hasattr(self.parent(), "close_all"):
                        self.parent().close_all()
                    else:
                        self.parent().on_dismiss.emit()
                        self.parent().close()
                except:
                    pass

    def mousePressEvent(self, event):
        """Make all bubbles transparent on click to see text behind."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.parent() and hasattr(self.parent(), "set_all_bubbles_opacity"):
                self.parent().set_all_bubbles_opacity(0.01)
            else:
                self.setWindowOpacity(0.01)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Restore opacity on release."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.parent() and hasattr(self.parent(), "set_all_bubbles_opacity"):
                self.parent().set_all_bubbles_opacity(1.0)
            else:
                self.setWindowOpacity(1.0)
        super().mouseReleaseEvent(event)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(300)  # Limit width for better wrapping

        # Apply styles
        self.label.setStyleSheet(
            f"color: {self.text_color.name()}; font-size: {self.font_size}px; font-family: 'Segoe UI', sans-serif;"
        )

        layout.addWidget(self.label)
        self.setLayout(layout)

        # Adjust size based on content
        self.adjustSize()

        # Position bubble exactly where the text was, with smart positioning
        self.position_bubble()

    def position_bubble(self):
        """Position the bubble at the exact location of the original text."""
        # Get screen geometry
        screen = QApplication.primaryScreen().virtualGeometry()

        # Target position (exact overlay)
        target_x = self.target_rect.x()
        target_y = self.target_rect.y()

        # Ensure it fits on screen horizontally
        if target_x < 0:
            target_x = 0
        if target_x + self.width() > screen.width():
            target_x = screen.width() - self.width()

        # Ensure it fits on screen vertically
        if target_y < 0:
            target_y = 0
        if target_y + self.height() > screen.height():
            target_y = screen.height() - self.height()

        # Move to calculated position (global coordinates)
        self.move(int(target_x), int(target_y))

        # Resize bubble to at least match the width of the original text area if the text is short
        # This helps cover the original text better
        if self.width() < self.target_rect.width():
            self.setMinimumWidth(self.target_rect.width())

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

    def __init__(self, config=None):  # Accept config
        super().__init__()
        self.config = config
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, False
        )  # Allow mouse events by default

        self.mode = "SELECT"  # SELECT, EDIT, DISPLAY
        self.selection_rect = QRect()
        self.is_drawing = False
        self.active_handle = None  # 'tl', 'tr', 'bl', 'br', 'move', None
        self.drag_start_pos = QPoint()
        self.rect_start_geo = QRect()

        self.bubbles = []

        # Double click detection
        self.last_click_time = 0
        self.double_click_threshold = 300  # milliseconds
        self.bubbles_opacity_reduced = False

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
        self.hide_loading()  # Hide loading when changing mode

        if mode == "DISPLAY":
            self.setCursor(Qt.CursorShape.ArrowCursor)
            # Enable mouse events in DISPLAY mode to allow "click anywhere to hide"
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)
            # Enable mouse events for SELECT and EDIT modes
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.update()

    def clear_bubbles(self):
        for bubble in self.bubbles:
            bubble.close()
        self.bubbles = []

    def set_all_bubbles_opacity(self, opacity):
        """Set opacity for all active bubbles."""
        for bubble in self.bubbles:
            bubble.setWindowOpacity(opacity)

    def set_initial_rect(self, rect):
        if rect:
            self.selection_rect = rect
            self.mode = "EDIT"
            self.update_controls_pos()
            self.controls.show()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

    def add_bubble(self, text, x, y, w, h):
        import time

        print(
            f"[{time.strftime('%H:%M:%S')}] [OVERLAY] Criando bubble: posição=({x}, {y}), tamanho=({w}, {h})"
        )
        # x, y are global screen coordinates
        # Create bubble as a top-level window so it can be positioned absolutely, but with parent for lifecycle
        bubble = TranslationBubble(text, x, y, w, h, self, self.config)

        # Adjust position to avoid overlap with existing bubbles
        self.adjust_bubble_position(bubble)

        bubble.show()
        self.bubbles.append(bubble)
        print(
            f"[{time.strftime('%H:%M:%S')}] [OVERLAY] Bubble criado e exibido. Total de bubbles: {len(self.bubbles)}"
        )

    def adjust_bubble_position(self, new_bubble):
        """Adjust bubble position to avoid overlap with existing bubbles."""
        if not self.bubbles:
            return

        new_rect = new_bubble.geometry()
        margin = 10  # Minimum margin between bubbles

        for existing_bubble in self.bubbles:
            existing_rect = existing_bubble.geometry()

            # Check if bubbles overlap
            if new_rect.intersects(existing_rect):
                # Move new bubble down and to the right
                new_x = existing_rect.right() + margin
                new_y = existing_rect.top()

                # Check if new position is still on screen
                screen = QApplication.primaryScreen().virtualGeometry()
                if new_x + new_rect.width() > screen.width():
                    # Try moving to the left of existing bubble
                    new_x = existing_rect.left() - new_rect.width() - margin
                    if new_x < 0:
                        # If still doesn't fit, move down
                        new_x = new_bubble.target_rect.x()
                        new_y = existing_rect.bottom() + margin

                if new_y + new_rect.height() > screen.height():
                    new_y = screen.height() - new_rect.height() - margin

                new_bubble.move(int(new_x), int(new_y))
                break

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
        s = 10  # Handle size
        return {
            "tl": QRect(r.left() - s // 2, r.top() - s // 2, s, s),
            "tr": QRect(r.right() - s // 2, r.top() - s // 2, s, s),
            "bl": QRect(r.left() - s // 2, r.bottom() - s // 2, s, s),
            "br": QRect(r.right() - s // 2, r.bottom() - s // 2, s, s),
        }

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background - only show overlay when selecting/editing
        if self.mode == "SELECT" or self.mode == "EDIT":
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        else:
            # DISPLAY mode: transparent/click-through background
            painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

        if (
            self.mode == "SELECT" or self.mode == "EDIT"
        ) and not self.selection_rect.isEmpty():
            # Clear rect area
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.selection_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )

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
        import time

        current_time = int(time.time() * 1000)  # Get current time in milliseconds

        # Check for double click
        time_since_last_click = current_time - self.last_click_time
        is_double_click = time_since_last_click < self.double_click_threshold
        self.last_click_time = current_time

        # Handle double click - close everything
        if is_double_click and self.bubbles and self.mode == "DISPLAY":
            self.on_dismiss.emit()
            self.close_all()
            return

        if self.mode == "DISPLAY":
            # Toggle opacity on any click
            if self.bubbles_opacity_reduced:
                self.set_all_bubbles_opacity(1.0)
                self.bubbles_opacity_reduced = False
            else:
                self.set_all_bubbles_opacity(0.01)
                self.bubbles_opacity_reduced = True
            return

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
                self.active_handle = "move"
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
            if handles["tl"].contains(pos) or handles["br"].contains(pos):
                cursor = Qt.CursorShape.SizeFDiagCursor
            elif handles["tr"].contains(pos) or handles["bl"].contains(pos):
                cursor = Qt.CursorShape.SizeBDiagCursor
            elif self.selection_rect.contains(pos):
                cursor = Qt.CursorShape.SizeAllCursor
            self.setCursor(cursor)

        if self.active_handle:
            delta = pos - self.drag_start_pos
            r = self.rect_start_geo

            if self.active_handle == "move":
                self.selection_rect.moveTo(r.topLeft() + delta)
            elif self.active_handle == "tl":
                self.selection_rect.setTopLeft(r.topLeft() + delta)
            elif self.active_handle == "tr":
                self.selection_rect.setTopRight(r.topRight() + delta)
            elif self.active_handle == "bl":
                self.selection_rect.setBottomLeft(r.bottomLeft() + delta)
            elif self.active_handle == "br":
                self.selection_rect.setBottomRight(r.bottomRight() + delta)

            self.selection_rect = self.selection_rect.normalized()
            self.update_controls_pos()
            self.update()

        elif self.is_drawing:
            self.selection_rect = QRect(self.drag_start_pos, pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.mode == "DISPLAY":
            return

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

        if y < 0:
            y = 0
        if y + ch > self.height():
            y = self.height() - ch

        self.controls.move(x, y)

    def close_all(self):
        """Close overlay and all bubbles."""
        self.clear_bubbles()
        self.close()

    def closeEvent(self, event):
        """Clean up bubbles when overlay is closed."""
        self.clear_bubbles()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.on_dismiss.emit()
            self.close_all()
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            if self.mode == "EDIT":
                self.confirm_selection()
