import sys
import os
import threading
import datetime
import keyboard
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QRect, QRunnable
from ui.floating_widget import FloatingWidget
from ui.settings_window import SettingsWindow
from ui.logs_window import LogsWindow
from ui.overlay_window import OverlayWindow
from core.config import ConfigManager
from core.capture import ScreenCapture
from core.ocr import OCRProcessor
from core.translator import TranslationService

class WorkerSignals(QObject):
    result_ready = pyqtSignal(str, str, str, int, int, int, int) # original, translated, image_path, x, y, w, h
    finished = pyqtSignal()
    error = pyqtSignal(str)

class PipelineWorker(QRunnable):
    def __init__(self, image, x, y, ocr_processor, translator, config):
        super().__init__()
        self.image = image
        self.x = x
        self.y = y
        self.ocr_processor = ocr_processor
        self.translator = translator
        self.config = config
        self.signals = WorkerSignals()

    def run(self):
        try:
            # Save image for logs
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            captures_dir = os.path.join(os.getcwd(), "captures")
            os.makedirs(captures_dir, exist_ok=True)
            image_path = os.path.join(captures_dir, f"capture_{timestamp}.png")
            self.image.save(image_path)

            # OCR
            ocr_results = self.ocr_processor.process_image(self.image)

            # Calculate bounding box of all detected text
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            
            full_text = []
            for item in ocr_results:
                full_text.append(item['text'])
                bbox = item['bbox']
                # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                # We need min/max of all points
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                min_x = min(min_x, min(xs))
                min_y = min(min_y, min(ys))
                max_x = max(max_x, max(xs))
                max_y = max(max_y, max(ys))
            
            original_text = "\n".join(full_text)
            
            if not original_text.strip():
                # No text found
                print("DEBUG: No text found in OCR results.")
                self.signals.finished.emit()
                return

            print(f"DEBUG: OCR found text: {original_text[:50]}...")

            # Translate
            source_lang = self.config.get("source_language", "en")
            target_lang = self.config.get("target_language", "pt")
            translated_text = self.translator.translate(original_text, source_lang=source_lang, target_lang=target_lang)
            
            # Pass the calculated text bounding box (relative to image) + offset (self.x, self.y)
            # We want the bubble to be at the top-left of the TEXT, not the image.
            text_x = self.x + int(min_x)
            text_y = self.y + int(min_y)
            text_w = int(max_x - min_x)
            text_h = int(max_y - min_y)
            
            self.signals.result_ready.emit(original_text, translated_text, image_path, text_x, text_y, text_w, text_h)
        except Exception as e:
            print(f"Error in pipeline: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.signals.finished.emit()

class MainController(QObject):
    sig_trigger_translate = pyqtSignal()
    sig_dismiss_overlay = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.ocr_processor = None 
        self.translator = TranslationService(self.config)
        
        self.is_defining_only = False
        
        self.floating_widget = FloatingWidget()
        self.settings_window = None
        self.logs_window = None
        self.overlay_window = None

        self.floating_widget.request_settings.connect(self.open_settings)
        self.floating_widget.request_logs.connect(self.open_logs)
        self.floating_widget.request_translate.connect(self.trigger_translate)

        
        # Connect internal signals for thread safety
        self.sig_trigger_translate.connect(self.trigger_translate)
        self.sig_dismiss_overlay.connect(self.dismiss_overlay)
        
        self.floating_widget.show()

        keyboard.add_hotkey('ctrl+z', self.trigger_translate_hotkey)
        keyboard.add_hotkey('esc', self.dismiss_overlay_hotkey)
        
        # Init OCR in background
        threading.Thread(target=self.init_ocr).start()

    def init_ocr(self):
        print("Initializing OCR...")
        lang = self.config.get("source_language", "en")
        self.ocr_processor = OCRProcessor(lang=lang)
        print(f"OCR Initialized with language: {lang}")

    def trigger_translate_hotkey(self):
        self.sig_trigger_translate.emit()

    def dismiss_overlay_hotkey(self):
        self.sig_dismiss_overlay.emit()

    def open_settings(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.settings_saved.connect(self.reload_ocr)
            self.settings_window.request_define_crop.connect(self.reset_crop_selection)
        self.settings_window.show()

    def reload_ocr(self):
        # Reload OCR in background
        print("Reloading OCR...")
        self.ocr_processor = None
        threading.Thread(target=self.init_ocr).start()

    def open_logs(self):
        if not self.logs_window:
            self.logs_window = LogsWindow(self.config)
        else:
            self.logs_window.refresh_logs()
        self.logs_window.show()

    def trigger_translate(self, force_new_selection=False):
        mode = self.config.get("default_capture_mode", "global")
        
        if not self.overlay_window:
            self.overlay_window = OverlayWindow(self.config)
            self.overlay_window.on_selection_complete.connect(self.process_crop_capture)
            self.overlay_window.on_dismiss.connect(self.dismiss_overlay)
        
        screen_geometry = QApplication.primaryScreen().virtualGeometry()
        self.overlay_window.setGeometry(screen_geometry)
        
        if mode == "crop":
            last_rect = self.config.get("last_crop_region")
            
            if last_rect and not force_new_selection:
                # Quick Crop: Use saved region immediately without showing overlay
                # But wait, user said "button that we already leave this crop pre-defined"
                # and "only need to adjust again if the person wants to".
                # So if I press Translate (Ctrl+Z), it should just translate that area?
                # Yes, "all other captures will not need to adjust it again".
                
                # So we skip the overlay selection and go straight to processing.
                rect = QRect(last_rect[0], last_rect[1], last_rect[2], last_rect[3])
                self.process_crop_capture(rect)
                return

            # If no last rect or forced new selection, show selection UI
            if last_rect:
                 # If we are forcing new selection but have a last rect, maybe show it for editing?
                 # For now, let's just let them draw new.
                 # Or better, show the old one for adjustment.
                 rect = QRect(last_rect[0], last_rect[1], last_rect[2], last_rect[3])
                 self.overlay_window.set_initial_rect(rect)
            else:
                 self.overlay_window.set_mode("SELECT")

            self.overlay_window.show()
            self.overlay_window.activateWindow()
        else:
            self.overlay_window.set_mode("DISPLAY")
            self.overlay_window.show()
            self.overlay_window.activateWindow()
            self.process_global_capture()

    def reset_crop_selection(self):
        # Force new selection for definition only
        self.is_defining_only = True
        self.trigger_translate(force_new_selection=True)

    def dismiss_overlay(self):
        self.is_defining_only = False
        if self.overlay_window:
            self.overlay_window.close()
            self.overlay_window = None

    def process_crop_capture(self, rect):
        # Save rect
        self.config.set("last_crop_region", [rect.x(), rect.y(), rect.width(), rect.height()])
        
        if self.is_defining_only:
            self.is_defining_only = False
            self.overlay_window.set_mode("DISPLAY")
            self.dismiss_overlay()
            return

        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        image = ScreenCapture.capture_screen((x, y, w, h))
        self.overlay_window.set_mode("DISPLAY")
        self.overlay_window.show() # Ensure window is visible
        self.overlay_window.show_loading(rect)
        self.start_worker(image, x, y)

    def process_global_capture(self):
        image = ScreenCapture.capture_screen()
        self.overlay_window.show_loading()
        self.start_worker(image, 0, 0)

    def start_worker(self, image, x, y):
        if not self.ocr_processor:
            print("OCR is still initializing...")
            # Optionally show a toast or message
            return

        self.thread = threading.Thread(target=self._run_worker, args=(image, x, y))
        self.thread.start()

    def _run_worker(self, image, x, y):
        # This runs in a thread.
        # We can't use QThread easily without moving object to thread.
        # But we can use signals if we connect them properly.
        # Let's use the Worker class logic but run it here and emit signals.
        # Actually, let's just use the logic directly here but emit signals to update UI.
        # We need a signal defined in MainController to update UI.
        
        # Wait, MainController is in the main thread.
        # If we define a signal on MainController, and emit it from this thread, it should be queued to main thread.
        
        worker = PipelineWorker(image, x, y, self.ocr_processor, self.translator, self.config)
        worker.signals.result_ready.connect(self.handle_result)
        worker.signals.finished.connect(self.handle_finished)
        worker.run()

    def handle_finished(self):
        if self.overlay_window:
            self.overlay_window.hide_loading()

    def handle_result(self, original, translated, image_path, x, y, w, h):
        # This slot should be called in the main thread if connected properly?
        # If the signal is emitted from a thread, and the receiver is in main thread, it works.
        if self.overlay_window:
            self.overlay_window.add_bubble(translated, x, y, w, h)
        
        # Add to history
        self.config.log_history(original, translated, image_path)
        
        if self.logs_window:
            self.logs_window.add_log(original, translated, image_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = MainController()
    
    # We need to handle the threading result properly. 
    # I'll modify MainController to have a signal for adding bubbles.
    
    sys.exit(app.exec())
