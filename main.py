import sys
import os
import threading
import datetime
import keyboard
import time
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QAction, QPen
from PyQt6.QtCore import QObject, pyqtSignal, QRect, QRunnable, QThreadPool, Qt
from ui.floating_widget import FloatingWidget
from ui.settings_window import SettingsWindow
from ui.logs_window import LogsWindow
from ui.overlay_window import OverlayWindow
from core.config import ConfigManager
from core.capture import ScreenCapture
from core.ocr import OCRProcessor
from core.translator import TranslationService


class WorkerSignals(QObject):
    result_ready = pyqtSignal(list)
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
            print(f"[{time.strftime('%H:%M:%S')}] [WORKER] Iniciando processamento...")
            print(
                f"[{time.strftime('%H:%M:%S')}] [WORKER] Região: x={self.x}, y={self.y}, imagem size={self.image.size if self.image else 'None'}"
            )

            # OCR
            print(f"[{time.strftime('%H:%M:%S')}] [WORKER] Executando OCR...")
            ocr_start = time.time()
            ocr_results = self.ocr_processor.process_image(self.image)
            ocr_time = time.time() - ocr_start
            print(
                f"[{time.strftime('%H:%M:%S')}] [WORKER] OCR concluído em {ocr_time:.2f}s. Textos detectados: {len(ocr_results) if ocr_results else 0}"
            )

            if not ocr_results:
                print(
                    f"[{time.strftime('%H:%M:%S')}] [WORKER] Nenhum texto encontrado. Finalizando."
                )
                self.signals.finished.emit()
                return

            # Process each detected text separately
            results = []
            source_lang = self.config.get("source_language", "en")
            target_lang = self.config.get("target_language", "pt")
            provider = self.config.get("default_provider", "mymemory")
            print(
                f"[{time.strftime('%H:%M:%S')}] [WORKER] Configuração: {source_lang} -> {target_lang} (provider: {provider})"
            )

            # Pre-process all text items to get valid texts and their bboxes
            text_items = []
            for idx, item in enumerate(ocr_results):
                original_text = item["text"].strip()
                if not original_text:
                    continue

                bbox = item["bbox"]
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                min_x = min(xs)
                min_y = min(ys)
                max_x = max(xs)
                max_y = max(ys)

                text_items.append(
                    {
                        "original": original_text,
                        "min_x": min_x,
                        "min_y": min_y,
                        "max_x": max_x,
                        "max_y": max_y,
                    }
                )

            if not text_items:
                print(
                    f"[{time.strftime('%H:%M:%S')}] [WORKER] Nenhum texto válido encontrado."
                )
                self.signals.finished.emit()
                return

            # BATCH TRANSLATION
            print(
                f"[{time.strftime('%H:%M:%S')}] [WORKER] Traduzindo {len(text_items)} textos em lote..."
            )
            translate_start = time.time()

            all_texts = [item["original"] for item in text_items]
            translated_texts = self.translator.translate_batch(
                all_texts,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=provider,
            )

            translate_time = time.time() - translate_start
            print(
                f"[{time.strftime('%H:%M:%S')}] [WORKER] Tradução em lote concluída em {translate_time:.2f}s"
            )

            # Build results with translated texts
            for idx, item in enumerate(text_items):
                translated_text = (
                    translated_texts[idx]
                    if idx < len(translated_texts)
                    else item["original"]
                )

                text_x = self.x + int(item["min_x"])
                text_y = self.y + int(item["min_y"])
                text_w = int(item["max_x"] - item["min_x"])
                text_h = int(item["max_y"] - item["min_y"])

                results.append(
                    {
                        "original": item["original"],
                        "translated": translated_text,
                        "image_data": self.image,
                        "x": text_x,
                        "y": text_y,
                        "w": text_w,
                        "h": text_h,
                    }
                )

            if results:
                print(
                    f"[{time.strftime('%H:%M:%S')}] [WORKER] Processamento concluído! {len(results)} bubble(s) criado(s)."
                )
                self.signals.result_ready.emit(results)
            else:
                print(
                    f"[{time.strftime('%H:%M:%S')}] [WORKER] Nenhum texto válido encontrado após processamento."
                )
                self.signals.finished.emit()
        except Exception as e:
            print(
                f"[{time.strftime('%H:%M:%S')}] [WORKER] ERRO CRÍTICO no pipeline: {e}"
            )
            import traceback

            traceback.print_exc()
            self.signals.error.emit(str(e))
        finally:
            print(f"[{time.strftime('%H:%M:%S')}] [WORKER] Finalizando worker.")
            self.signals.finished.emit()


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
                self.overlay_window.activateWindow()
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
            print(
                f"[{time.strftime('%H:%M:%S')}] [MAIN] ERRO: OCR ainda está inicializando. Aguarde..."
            )
            return

        print(f"[{time.strftime('%H:%M:%S')}] [MAIN] Iniciando worker thread...")
        self.thread = threading.Thread(
            target=self._run_worker, args=(image, x, y), daemon=True
        )
        self.thread.start()

    def _run_worker(self, image, x, y):
        print(f"[{time.strftime('%H:%M:%S')}] [THREAD] Worker thread iniciada.")
        worker = PipelineWorker(
            image, x, y, self.ocr_processor, self.translator, self.config
        )
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

        if image_data:
            self.config.log_history(all_original, all_translated, image_data)

        if self.logs_window:
            self.logs_window.add_log(all_original, all_translated, image_data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = MainController()
    sys.exit(app.exec())
