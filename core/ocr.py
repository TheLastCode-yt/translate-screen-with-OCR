from paddleocr import PaddleOCR
import numpy as np

class OCRProcessor:
    def __init__(self, lang='en'):
        self.lang_map = {
            'en': 'en',
            'zh': 'ch',
            'ja': 'japan',
            'ko': 'korean',
            'fr': 'french',
            'de': 'german',
            'it': 'it',
            'ru': 'ru',
            'es': 'es',
            'pt': 'pt'
        }
        paddle_lang = self.lang_map.get(lang, 'en')
        self.ocr = PaddleOCR(use_angle_cls=True, lang=paddle_lang)

    def process_image(self, image):
        """
        Process the image and return detected text and bounding boxes.
        :param image: PIL Image
        :return: List of tuples (text, confidence, bbox)
        """
        # PaddleOCR expects numpy array (opencv format), usually BGR
        import cv2
        img_array = np.array(image)
        
        # Convert RGB to BGR if it's RGB (PIL default)
        if img_array.ndim == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # PaddleOCR result structure: [[[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence)], ...]
        # OR dictionary structure (PaddleX): [{'rec_texts': [], 'dt_polys': [], ...}]
        result = self.ocr.ocr(img_array)
        print(f"DEBUG: Raw OCR result: {result}")
        
        parsed_results = []
        if result and len(result) > 0:
            # Check for Dictionary format (PaddleX / New PaddleOCR)
            if isinstance(result[0], dict):
                data = result[0]
                texts = data.get('rec_texts', [])
                scores = data.get('rec_scores', [])
                boxes = data.get('dt_polys', [])
                
                for i, text in enumerate(texts):
                    confidence = scores[i] if i < len(scores) else 1.0
                    bbox = boxes[i] if i < len(boxes) else []
                    
                    # Convert numpy array to list if needed
                    if hasattr(bbox, 'tolist'):
                        bbox = bbox.tolist()
                    
                    parsed_results.append({
                        "text": text,
                        "confidence": confidence,
                        "bbox": bbox
                    })
            
            # Check for List format (Legacy PaddleOCR)
            elif isinstance(result[0], list):
                for line in result[0]:
                    print(f"DEBUG: Processing line: {line}")
                    if len(line) >= 2:
                        bbox = line[0]
                        content = line[1]
                        
                        # Validate bbox structure: Must be list of 4 points
                        # bbox can be list or numpy array
                        if len(bbox) != 4:
                            print(f"DEBUG: Skipping line due to bbox length: {len(bbox)}")
                            continue

                        if isinstance(content, (list, tuple)) and len(content) >= 2:
                            text, confidence = content[0], content[1]
                        else:
                            # Fallback if structure is different
                            text = str(content)
                            confidence = 1.0
                        
                        parsed_results.append({
                            "text": text,
                            "confidence": confidence,
                            "bbox": bbox 
                        })
        else:
            print("DEBUG: No text detected by PaddleOCR.")
        
        return parsed_results
