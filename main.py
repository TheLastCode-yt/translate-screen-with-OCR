import sys
import os
import threading
import datetime
import keyboard
import time
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QAction, QPen
from PyQt6.QtCore import QObject, pyqtSignal, QRect, QRunnable, QThreadPool, Qt, QEvent, QTimer
from ui.floating_widget import FloatingWidget
from ui.settings_window import SettingsWindow
from ui.logs_window import LogsWindow
from ui.overlay_window import OverlayWindow
from core.config import ConfigManager
from core.capture import ScreenCapture
from core.ocr import OCRProcessor
from core.translator import TranslationService
from core.pipeline import PipelineWorker





class MainController(QObject):
    sig_trigger_translate = pyqtSignal()
    sig_dismiss_overlay = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.ocr_processor = None
        self.ocr_lock = threading.Lock()
        self.translator = TranslationService(self.config)
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(4)

        self.is_defining_only = (
            False  # Flag para controlar se está apenas definindo a área
        )

        self.floating_widget = FloatingWidget()
        self.settings_window = None
        self.logs_window = None
        self.overlay_window = None
        self.current_worker = None  # Track current worker for cancellation

        self.floating_widget.request_settings.connect(self.open_settings)
        self.floating_widget.request_logs.connect(self.open_logs)
        self.floating_widget.request_translate.connect(self.trigger_translate)

        # Connect internal signals for thread safety
        self.sig_trigger_translate.connect(self.trigger_translate)
        self.sig_dismiss_overlay.connect(self.dismiss_overlay)

        self.floating_widget.show()

        keyboard.add_hotkey("ctrl+z", self.trigger_translate_hotkey)
        keyboard.add_hotkey("esc", self.dismiss_overlay_hotkey)

        # Init OCR in background
        threading.Thread(target=self.init_ocr, daemon=True).start()

        # Setup System Tray
        self.setup_tray_icon()

        # Install global event filter
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            print(f"[{time.strftime('%H:%M:%S')}] [MAIN] ESC pressionado (EventFilter)")
            # Only dismiss if overlay is active
            if self.overlay_window and self.overlay_window.isVisible():
                self.sig_dismiss_overlay.emit()
                return True
        return super().eventFilter(obj, event)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.create_tray_icon())

        # Tray Menu
        tray_menu = QMenu()

        action_translate = QAction("Traduzir (Ctrl+Z)", self)
        action_translate.triggered.connect(self.trigger_translate_hotkey)
        tray_menu.addAction(action_translate)

        action_settings = QAction("Configurações", self)
        action_settings.triggered.connect(self.open_settings)
        tray_menu.addAction(action_settings)

        action_logs = QAction("Logs", self)
        action_logs.triggered.connect(self.open_logs)
        tray_menu.addAction(action_logs)

        tray_menu.addSeparator()

        action_quit = QAction("Sair", self)
        action_quit.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(action_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def create_tray_icon(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.setBrush(QBrush(QColor("#4CAF50")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 64, 64, 12, 12)

        # Text
        painter.setPen(QPen(QColor("white")))
        font = painter.font()
        font.setPixelSize(40)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")

        painter.end()
        return QIcon(pixmap)

    def init_ocr(self):
        print("[MAIN] Inicializando OCR...")
        lang = self.config.get("source_language", "en")
        self.ocr_processor = OCRProcessor(lang=lang)
        print(f"[MAIN] OCR Inicializado com idioma: {lang} e warm-up executado!")
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage("Tradutor", "OCR Pronto!", QSystemTrayIcon.MessageIcon.Information, 2000)

    def trigger_translate_hotkey(self):
        self.sig_trigger_translate.emit()

    def dismiss_overlay_hotkey(self):
        print(f"[{time.strftime('%H:%M:%S')}] [MAIN] ESC pressionado (Global Hotkey)")
        self.sig_dismiss_overlay.emit()

    def open_settings(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.settings_saved.connect(self.reload_ocr)
            self.settings_window.request_define_crop.connect(
                self.open_crop_definition
            )  # MUDANÇA AQUI
        self.settings_window.show()

    def reload_ocr(self):
        print("Reloading OCR...")
        self.ocr_processor = None
        threading.Thread(target=self.init_ocr, daemon=True).start()

    def open_logs(self):
        if not self.logs_window:
            self.logs_window = LogsWindow(self.config)
        else:
            self.logs_window.refresh_logs()
        self.logs_window.show()

    def open_crop_definition(self):
        """Abre o overlay APENAS para definir a área de crop, sem traduzir"""
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] ===== DEFININDO ÁREA DE CROP ====="
        )

        # Seta o flag ANTES de fazer qualquer coisa
        self.is_defining_only = True

        if not self.overlay_window:
            print(
                f"[{time.strftime('%H:%M:%S')}] [MAIN] Criando overlay window para definição..."
            )
            self.overlay_window = OverlayWindow(self.config)
            self.overlay_window.on_selection_complete.connect(
                self.handle_crop_definition
            )  # Conecta ao handler específico
            self.overlay_window.on_dismiss.connect(self.dismiss_overlay)
        else:
            # Se já existe, reconecta ao handler de definição
            try:
                self.overlay_window.on_selection_complete.disconnect()
            except:
                pass
            self.overlay_window.on_selection_complete.connect(
                self.handle_crop_definition
            )

        screen_geometry = QApplication.primaryScreen().virtualGeometry()
        self.overlay_window.setGeometry(screen_geometry)

        # Verifica se já existe uma região salva para mostrar como preview
        last_rect = self.config.get("last_crop_region")
        if last_rect:
            rect = QRect(last_rect[0], last_rect[1], last_rect[2], last_rect[3])
            self.overlay_window.set_initial_rect(rect)
        else:
            self.overlay_window.set_mode("SELECT")

        self.overlay_window.show()
        self.overlay_window.activateWindow()
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Overlay aberto para definição de área."
        )

    def handle_crop_definition(self, rect):
        """Handler específico para quando está APENAS definindo a área"""
        print(f"[{time.strftime('%H:%M:%S')}] [MAIN] Salvando área de crop definida...")

        # Salva a região
        self.config.set(
            "last_crop_region", [rect.x(), rect.y(), rect.width(), rect.height()]
        )
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Região salva: x={rect.x()}, y={rect.y()}, w={rect.width()}, h={rect.height()}"
        )

        # Reseta o flag e fecha o overlay
        self.is_defining_only = False
        if self.overlay_window:
            self.overlay_window.close()
            self.overlay_window = None

        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Área de crop definida com sucesso! Use Ctrl+Z para traduzir."
        )

    def trigger_translate(self, force_new_selection=False):
        """Trigger para realizar tradução (não confundir com definição de área)"""
        print(f"[{time.strftime('%H:%M:%S')}] [MAIN] ===== TRADUÇÃO SOLICITADA =====")
        mode = self.config.get("default_capture_mode", "global")
        print(f"[{time.strftime('%H:%M:%S')}] [MAIN] Modo de captura: {mode}")

        if not self.overlay_window:
            print(f"[{time.strftime('%H:%M:%S')}] [MAIN] Criando overlay window...")
            self.overlay_window = OverlayWindow(self.config)
            self.overlay_window.on_selection_complete.connect(self.process_crop_capture)
            self.overlay_window.on_dismiss.connect(self.dismiss_overlay)
        else:
            # Garante que está conectado ao handler correto de tradução
            try:
                self.overlay_window.on_selection_complete.disconnect()
            except:
                pass
            self.overlay_window.on_selection_complete.connect(self.process_crop_capture)

        screen_geometry = QApplication.primaryScreen().virtualGeometry()
        self.overlay_window.setGeometry(screen_geometry)

        if mode == "crop":
            last_rect = self.config.get("last_crop_region")

            # Se forçar nova seleção OU não tiver região salva
            if force_new_selection or not last_rect:
                print(
                    f"[{time.strftime('%H:%M:%S')}] [MAIN] Mostrando interface de seleção..."
                )
                if last_rect:
                    rect = QRect(last_rect[0], last_rect[1], last_rect[2], last_rect[3])
                    self.overlay_window.set_initial_rect(rect)
                else:
                    self.overlay_window.set_mode("SELECT")
                self.overlay_window.show()
                QTimer.singleShot(100, self.overlay_window.activateWindow)
                return

            # Se tem região salva, usa diretamente
            print(
                f"[{time.strftime('%H:%M:%S')}] [MAIN] Usando região salva: {last_rect}"
            )
            rect = QRect(last_rect[0], last_rect[1], last_rect[2], last_rect[3])
            self.process_crop_capture(rect)
        else:
            # Modo global
            print(
                f"[{time.strftime('%H:%M:%S')}] [MAIN] Modo global - capturando tela inteira..."
            )
            self.overlay_window.set_mode("DISPLAY")
            self.overlay_window.show()
            self.overlay_window.activateWindow()
            self.process_global_capture()

    def dismiss_overlay(self):
        self.is_defining_only = False
        self.cancel_current_worker()  # Cancel worker on dismiss
        if self.overlay_window:
            self.overlay_window.close()
            self.overlay_window = None

    def process_crop_capture(self, rect):
        """Processa a captura E tradução de uma região"""
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Processando captura de região para TRADUÇÃO..."
        )

        # Salva a região (caso seja uma nova seleção)
        self.config.set(
            "last_crop_region", [rect.x(), rect.y(), rect.width(), rect.height()]
        )

        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Capturando região: x={x}, y={y}, w={w}, h={h}"
        )

        capture_start = time.time()
        image = ScreenCapture.capture_screen((x, y, w, h))
        capture_time = time.time() - capture_start
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Captura concluída em {capture_time:.3f}s."
        )

        self.overlay_window.set_mode("DISPLAY")
        self.overlay_window.show()
        self.overlay_window.show_loading(rect)
        self.start_worker(image, x, y)

    def process_global_capture(self):
        print(f"[{time.strftime('%H:%M:%S')}] [MAIN] Capturando tela inteira...")
        capture_start = time.time()
        image = ScreenCapture.capture_screen()
        capture_time = time.time() - capture_start
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Captura concluída em {capture_time:.3f}s."
        )
        self.overlay_window.show_loading()
        self.start_worker(image, 0, 0)

    def start_worker(self, image, x, y):
        if not self.ocr_processor:
            msg = "OCR inicializando... Aguarde."
            print(f"[{time.strftime('%H:%M:%S')}] [MAIN] AVISO: {msg}")
            if hasattr(self, 'tray_icon'):
                self.tray_icon.showMessage("Tradutor", msg, QSystemTrayIcon.MessageIcon.Information, 1000)
            
            if self.overlay_window:
                self.overlay_window.show_loading()
            
            # Start a thread to wait for OCR
            threading.Thread(target=self._wait_and_run_worker, args=(image, x, y), daemon=True).start()
            return

        print(f"[{time.strftime('%H:%M:%S')}] [MAIN] Iniciando worker thread...")
        
        # Cancel previous worker if exists
        self.cancel_current_worker()

        self.thread = threading.Thread(
            target=self._run_worker, args=(image, x, y), daemon=True
        )
        self.thread.start()

    def cancel_current_worker(self):
        if self.current_worker:
            print(f"[{time.strftime('%H:%M:%S')}] [MAIN] Cancelando worker anterior...")
            self.current_worker.cancel()
            self.current_worker = None

    def _wait_and_run_worker(self, image, x, y):
        """Waits for OCR to be ready and then runs the worker"""
        print(f"[{time.strftime('%H:%M:%S')}] [THREAD] Aguardando OCR ficar pronto...")
        attempts = 0
        # Wait up to 30 seconds
        while self.ocr_processor is None and attempts < 60:
            time.sleep(0.5)
            attempts += 1
        
        if self.ocr_processor:
            print(f"[{time.strftime('%H:%M:%S')}] [THREAD] OCR pronto! Iniciando processamento.")
            self._run_worker(image, x, y)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] [THREAD] Timeout aguardando OCR.")

    def _run_worker(self, image, x, y):
        print(f"[{time.strftime('%H:%M:%S')}] [THREAD] Worker thread iniciada.")
        worker = PipelineWorker(
            image, x, y, self.ocr_processor, self.translator, self.config
        )
        self.current_worker = worker
        worker.signals.result_ready.connect(self.handle_result)
        worker.signals.finished.connect(self.handle_finished)
        worker.signals.error.connect(self.handle_error)
        worker.run()

    def handle_error(self, error_msg):
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] ERRO recebido do worker: {error_msg}"
        )

    def handle_finished(self):
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Worker finalizado. Ocultando loading..."
        )
        if self.overlay_window:
            self.overlay_window.hide_loading()

    def handle_result(self, results):
        print(
            f"[{time.strftime('%H:%M:%S')}] [MAIN] Resultado recebido: {len(results)} bubble(s)."
        )
        if not results:
            return

        all_original = "\n".join([r["original"] for r in results])
        all_translated = "\n".join([r["translated"] for r in results])
        image_data = results[0]["image_data"] if results else None

        if self.overlay_window:
            for idx, result in enumerate(results):
                self.overlay_window.add_bubble(
                    result["translated"],
                    result["x"],
                    result["y"],
                    result["w"],
                    result["h"],
                )
            
            # Force focus so ESC works immediately
            self.overlay_window.activateWindow()
            self.overlay_window.raise_()

        if image_data:
            self.config.log_history(all_original, all_translated, image_data)

        if self.logs_window:
            self.logs_window.add_log(all_original, all_translated, image_data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = MainController()
    sys.exit(app.exec())
