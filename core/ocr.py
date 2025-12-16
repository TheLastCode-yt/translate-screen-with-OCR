import numpy as np
import time
import cv2
import os
import sys
from collections import defaultdict

# Suppress all warnings and logs
os.environ["FLAGS_allocator_strategy"] = "auto_growth"
os.environ["GLOG_minloglevel"] = "2"
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")


class OCRProcessor:
    # Optimized for speed vs accuracy balance
    MAX_IMAGE_DIM = 1920

    def __init__(self, lang="en", reading_direction="auto"):
        """
        Initialize OCR processor
        :param lang: Language code (en, zh, ja, ko, etc)
        :param reading_direction: 'auto' (automatic), 'ltr' (left-to-right) or 'rtl' (right-to-left)
        """
        self.lang_map = {
            "en": "en",
            "zh": "ch",
            "ja": "japan",
            "ko": "korean",
            "fr": "french",
            "de": "german",
            "it": "it",
            "ru": "ru",
            "es": "es",
            "pt": "pt",
        }

        # Auto-detect reading direction based on language
        if reading_direction == "auto":
            # Japanese and traditional Chinese manga are read right-to-left
            if lang in ["ja", "zh"]:
                self.reading_direction = "rtl"
            else:
                # All other languages use left-to-right
                self.reading_direction = "ltr"
        else:
            self.reading_direction = reading_direction

        paddle_lang = self.lang_map.get(lang, "en")
        self.lang = lang

        print(
            f"[OCR] Inicializando idioma={paddle_lang}, direção={self.reading_direction} (auto-detectado)"
            if reading_direction == "auto"
            else f"[OCR] Inicializando idioma={paddle_lang}, direção={self.reading_direction}"
        )

        # Suppress stdout temporarily during initialization
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            # Redirect output during import and initialization
            sys.stdout = open(os.devnull, "w")
            sys.stderr = open(os.devnull, "w")

            from paddleocr import PaddleOCR

            # Initialize with performance parameters
            self.ocr = PaddleOCR(
                lang=paddle_lang,
                use_angle_cls=False,
                enable_mkldnn=True
            )

        except Exception as e:
            # Restore output to show error
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            print(f"[OCR] ERRO: {e}")
            print("[OCR] Tentando com configuração padrão...")

            try:
                from paddleocr import PaddleOCR

                # Performance optimization:
                # use_angle_cls=False: Significant speedup (assumes horizontal text)
                # enable_mkldnn=True: Accelerates CPU inference
                # show_log=False: Reduces I/O overhead
                self.ocr = PaddleOCR(
                    lang=paddle_lang,
                    use_angle_cls=False,
                    enable_mkldnn=True
                )
            except Exception as e2:
                print(f"[OCR] ERRO CRÍTICO: {e2}")
                raise
        finally:
            # Always restore output
            if sys.stdout != original_stdout:
                sys.stdout.close()
                sys.stdout = original_stdout
            if sys.stderr != original_stderr:
                sys.stderr.close()
                sys.stderr = original_stderr

        self.scale_factor = 1.0
        print("[OCR] Inicialização concluída")

        # Warm-up: Execute a primeira tradução para carregar o modelo na memória
        print("[OCR] Executando warm-up do modelo...")
        self._warmup()

    def _warmup(self):
        """Pre-warm o modelo PaddleOCR com uma imagem dummy"""
        try:
            import numpy as np

            # Cria uma imagem dummy pequena (100x100) com texto branco em fundo preto
            dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
            # Adiciona um retângulo branco para simular texto
            dummy_image[30:70, 30:70] = 255

            print("[OCR] Warm-up: Processando imagem dummy...")
            result = self.ocr.ocr(dummy_image)
            print(
                f"[OCR] Warm-up concluído! Resultado: {len(result) if result else 0} linhas detectadas"
            )
        except Exception as e:
            print(f"[OCR] AVISO: Warm-up falhou (não crítico): {e}")

    def _optimize_image(self, img_array):
        """Resize image if too large for better performance."""
        h, w = img_array.shape[:2]
        max_dim = max(h, w)

        if max_dim > self.MAX_IMAGE_DIM:
            self.scale_factor = self.MAX_IMAGE_DIM / max_dim
            new_w = int(w * self.scale_factor)
            new_h = int(h * self.scale_factor)
            img_array = cv2.resize(
                img_array, (new_w, new_h), interpolation=cv2.INTER_LINEAR
            )
            print(
                f"[OCR] Imagem redimensionada: {w}x{h} -> {new_w}x{new_h} (fator: {self.scale_factor:.2f})"
            )
        else:
            self.scale_factor = 1.0

        return img_array

    def process_image(self, image):
        """
        Process the image and return detected text and bounding boxes.
        :param image: PIL Image
        :return: List of dicts with text, confidence, bbox
        """
        start_time = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] [OCR] Iniciando processamento...")

        # Convert PIL to numpy array
        img_array = np.array(image)

        # Convert RGB to BGR if needed (PaddleOCR expects BGR)
        if img_array.ndim == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Optimize image size
        img_array = self._optimize_image(img_array)

        # Run OCR with error handling
        ocr_start = time.time()
        try:
            result = self.ocr.ocr(img_array)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [OCR] ERRO: {e}")
            return []

        ocr_time = time.time() - ocr_start
        print(
            f"[{time.strftime('%H:%M:%S')}] [OCR] PaddleOCR concluído em {ocr_time:.2f}s"
        )

        # Parse results
        parsed_results = self._parse_ocr_results(result)

        total_time = time.time() - start_time
        print(
            f"[{time.strftime('%H:%M:%S')}] [OCR] Processamento concluído: {len(parsed_results)} textos em {total_time:.2f}s"
        )

        # Group text into speech bubbles using clustering
        grouped_results = self._group_text_bubbles(parsed_results)
        print(
            f"[{time.strftime('%H:%M:%S')}] [OCR] Agrupamento: {len(parsed_results)} -> {len(grouped_results)} balões"
        )

        return grouped_results

    def _parse_ocr_results(self, result):
        """Parse OCR results handling both dictionary and list formats."""
        parsed_results = []

        if not result or len(result) == 0:
            return parsed_results

        # Handle Dictionary format (newer PaddleOCR)
        if isinstance(result[0], dict):
            data = result[0]
            texts = data.get("rec_texts", [])
            scores = data.get("rec_scores", [])
            boxes = data.get("dt_polys", [])

            for i, text in enumerate(texts):
                if not text or not text.strip():
                    continue

                confidence = scores[i] if i < len(scores) else 1.0
                bbox = boxes[i] if i < len(boxes) else []

                # Filter low confidence results
                if confidence < 0.5:
                    continue

                bbox = self._convert_bbox(bbox)

                parsed_results.append(
                    {"text": text, "confidence": confidence, "bbox": bbox}
                )

        # Handle List format (legacy PaddleOCR)
        elif isinstance(result[0], list):
            for line in result[0]:
                if not line or len(line) < 2:
                    continue

                bbox = line[0]
                content = line[1]

                # Validate bbox structure
                if not bbox or len(bbox) != 4:
                    continue

                # Extract text and confidence
                if isinstance(content, (list, tuple)) and len(content) >= 2:
                    text, confidence = content[0], content[1]
                else:
                    text = str(content)
                    confidence = 1.0

                if not text or not text.strip():
                    continue

                # Filter low confidence results
                if confidence < 0.5:
                    continue

                bbox = self._convert_bbox(bbox)

                parsed_results.append(
                    {"text": text, "confidence": confidence, "bbox": bbox}
                )

        return parsed_results

    def _convert_bbox(self, bbox):
        """Convert bbox to list format and scale if needed."""
        # Convert numpy array to list if needed
        if hasattr(bbox, "tolist"):
            bbox = bbox.tolist()

        # Scale bbox back if image was resized
        if self.scale_factor != 1.0:
            bbox = self._scale_bbox(bbox)

        return bbox

    def _scale_bbox(self, bbox):
        """Scale bounding box back to original image size."""
        if not bbox or self.scale_factor == 1.0:
            return bbox

        inv_scale = 1.0 / self.scale_factor
        return [[int(p[0] * inv_scale), int(p[1] * inv_scale)] for p in bbox]

    def _get_bbox_center(self, bbox):
        """Get center point of bounding box."""
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _get_bbox_coords(self, bbox):
        """Get min/max coordinates of bounding box."""
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        return min(xs), min(ys), max(xs), max(ys)

    def _calculate_distance(self, bbox1, bbox2):
        """Calculate distance between two bounding boxes."""
        x1_min, y1_min, x1_max, y1_max = self._get_bbox_coords(bbox1)
        x2_min, y2_min, x2_max, y2_max = self._get_bbox_coords(bbox2)

        # Calculate center points
        c1x, c1y = (x1_min + x1_max) / 2, (y1_min + y1_max) / 2
        c2x, c2y = (x2_min + x2_max) / 2, (y2_min + y2_max) / 2

        # Euclidean distance between centers
        return np.sqrt((c1x - c2x) ** 2 + (c1y - c2y) ** 2)

    def _boxes_overlap_or_close(self, bbox1, bbox2, threshold_multiplier=1.5):
        """Check if two boxes overlap or are close enough to be in same bubble."""
        x1_min, y1_min, x1_max, y1_max = self._get_bbox_coords(bbox1)
        x2_min, y2_min, x2_max, y2_max = self._get_bbox_coords(bbox2)

        # Calculate dimensions
        h1 = y1_max - y1_min
        h2 = y2_max - y2_min
        w1 = x1_max - x1_min
        w2 = x2_max - x2_min

        # Adaptive threshold based on box sizes
        avg_height = (h1 + h2) / 2
        avg_width = (w1 + w2) / 2

        # Thresholds
        y_threshold = avg_height * threshold_multiplier
        x_threshold = avg_width * threshold_multiplier

        # Check vertical proximity
        vertical_gap = max(0, max(y1_min, y2_min) - min(y1_max, y2_max))
        if vertical_gap > y_threshold:
            return False

        # Check horizontal proximity
        horizontal_gap = max(0, max(x1_min, x2_min) - min(x1_max, x2_max))
        if horizontal_gap > x_threshold:
            return False

        return True

    def _group_text_bubbles(self, results):
        """
        Group text boxes into speech bubbles using clustering algorithm.
        This handles multiple separate bubbles correctly.
        """
        if not results or len(results) <= 1:
            return results

        n = len(results)

        # Create adjacency list for grouping
        groups = []
        assigned = [False] * n

        # Build groups using connected components
        for i in range(n):
            if assigned[i]:
                continue

            # Start new group
            current_group = [i]
            assigned[i] = True
            queue = [i]

            while queue:
                current = queue.pop(0)

                # Check all unassigned boxes
                for j in range(n):
                    if assigned[j]:
                        continue

                    # Check if boxes should be in same group
                    if self._boxes_overlap_or_close(
                        results[current]["bbox"], results[j]["bbox"]
                    ):
                        current_group.append(j)
                        assigned[j] = True
                        queue.append(j)

            groups.append(current_group)

        # Create merged results for each group
        merged_results = []

        for group_indices in groups:
            if not group_indices:
                continue

            # Get all boxes in this group
            group_boxes = [results[i] for i in group_indices]

            # Sort boxes within group by reading order
            group_boxes = self._sort_by_reading_order(group_boxes)

            # Merge all text in the group
            merged_text = " ".join([box["text"] for box in group_boxes])

            # Calculate combined bounding box
            all_coords = []
            for box in group_boxes:
                all_coords.extend(box["bbox"])

            xs = [p[0] for p in all_coords]
            ys = [p[1] for p in all_coords]
            combined_bbox = [
                [min(xs), min(ys)],
                [max(xs), min(ys)],
                [max(xs), max(ys)],
                [min(xs), max(ys)],
            ]

            # Average confidence
            avg_confidence = sum([box["confidence"] for box in group_boxes]) / len(
                group_boxes
            )

            merged_results.append(
                {
                    "text": merged_text.strip(),
                    "confidence": avg_confidence,
                    "bbox": combined_bbox,
                }
            )

        # Sort final results by reading order (top to bottom, then left/right)
        merged_results = self._sort_bubbles_by_position(merged_results)

        return merged_results

    def _sort_by_reading_order(self, boxes):
        """Sort boxes within a bubble by reading order."""
        if not boxes:
            return boxes

        # Sort by Y position first (top to bottom), then by X
        def sort_key(box):
            x_min, y_min, _, _ = self._get_bbox_coords(box["bbox"])
            if self.reading_direction == "rtl":
                return (y_min, -x_min)  # Right to left (manga)
            else:
                return (y_min, x_min)  # Left to right

        return sorted(boxes, key=sort_key)

    def _sort_bubbles_by_position(self, bubbles):
        """Sort complete bubbles by their position in the page."""
        if not bubbles:
            return bubbles

        def sort_key(bubble):
            x_min, y_min, _, _ = self._get_bbox_coords(bubble["bbox"])
            # Primary sort by Y (top to bottom), secondary by X
            if self.reading_direction == "rtl":
                return (y_min, -x_min)  # Right to left for manga
            else:
                return (y_min, x_min)  # Left to right

        return sorted(bubbles, key=sort_key)
