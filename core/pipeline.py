import time
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable

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
        self.config = config
        self.signals = WorkerSignals()
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            print(f"[{time.strftime('%H:%M:%S')}] [WORKER] Iniciando processamento...")
            print(
                f"[{time.strftime('%H:%M:%S')}] [WORKER] Região: x={self.x}, y={self.y}, imagem size={self.image.size if self.image else 'None'}"
            )

            # Check cancellation before OCR
            if self.is_cancelled:
                print(f"[{time.strftime('%H:%M:%S')}] [WORKER] Cancelado antes do OCR.")
                self.signals.finished.emit()
                return

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

            # Check cancellation before Translation
            if self.is_cancelled:
                print(f"[{time.strftime('%H:%M:%S')}] [WORKER] Cancelado antes da tradução.")
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

            if self.is_cancelled:
                print(f"[{time.strftime('%H:%M:%S')}] [WORKER] Cancelado antes de emitir resultados.")
                self.signals.finished.emit()
                return

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
