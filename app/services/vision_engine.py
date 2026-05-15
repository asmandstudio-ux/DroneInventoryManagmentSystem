import os
import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
from pyzbar import pyzbar
from typing import List, Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class VisionEngine:
    def __init__(self):
        self.model: Optional[YOLO] = None
        self.reader = easyocr.Reader(['en'], gpu=False) # Set gpu=True if CUDA available
        self.label_template: Optional[np.ndarray] = None
        self.model_path = settings.VISION_MODEL_PATH
        self.template_path = settings.LABEL_TEMPLATE_PATH
        
        # Auto-load if exists
        if os.path.exists(self.model_path):
            self.load_model(self.model_path)
        
        if os.path.exists(self.template_path):
            self.load_template(self.template_path)

    def load_model(self, path: str) -> bool:
        """Load custom YOLOv8 weights"""
        try:
            if not os.path.exists(path):
                logger.error(f"Model path not found: {path}")
                return False
            self.model = YOLO(path)
            logger.info(f"YOLOv8 model loaded successfully from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {str(e)}")
            return False

    def load_template(self, path: str) -> bool:
        """Load reference label image for template matching"""
        try:
            if not os.path.exists(path):
                logger.error(f"Template path not found: {path}")
                return False
            self.label_template = cv2.imread(path)
            if self.label_template is None:
                raise ValueError("Could not read image file")
            logger.info(f"Label template loaded successfully from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load template: {str(e)}")
            return False

    def find_labels_by_template(self, image: np.ndarray, threshold: float = 0.7) -> List[Dict]:
        """Find regions matching the uploaded label template"""
        if self.label_template is None:
            return []
        
        results = []
        h, w = self.label_template.shape[:2]
        
        # Match template
        res = cv2.matchTemplate(image, self.label_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        
        # Non-maximum suppression (simple version)
        points = list(zip(*loc[::-1]))
        used_points = []
        
        for pt in points:
            is_new = True
            for used in used_points:
                dist = np.sqrt((pt[0]-used[0])**2 + (pt[1]-used[1])**2)
                if dist < 20: # Skip if too close to existing detection
                    is_new = False
                    break
            if is_new:
                used_points.append(pt)
                results.append({
                    "x": int(pt[0]),
                    "y": int(pt[1]),
                    "w": int(w),
                    "h": int(h),
                    "confidence": float(res[pt[1], pt[0]])
                })
        
        return results

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Main processing pipeline:
        1. Detect objects with YOLO (if model loaded) OR Template Matching
        2. Extract ROI
        3. Run OCR and Barcode Decoder on ROI
        """
        if not os.path.exists(image_path):
            return {"error": "Image file not found"}
        
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Could not read image"}
        
        detections = []
        
        # Strategy A: Use YOLO if model is loaded
        if self.model:
            yolo_results = self.model(image, verbose=False)
            for r in yolo_results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    class_name = self.model.names[cls]
                    
                    roi = image[y1:y2, x1:x2]
                    ocr_text, barcodes = self._analyze_roi(roi)
                    
                    detections.append({
                        "type": "yolo_object",
                        "class": class_name,
                        "confidence": conf,
                        "bbox": [x1, y1, x2-x1, y2-y1],
                        "extracted_text": ocr_text,
                        "barcodes": barcodes
                    })
        
        # Strategy B: Use Template Matching if no YOLO but template exists
        elif self.label_template is not None:
            template_dets = self.find_labels_by_template(image)
            for det in template_dets:
                x, y, w, h = det['x'], det['y'], det['w'], det['h']
                roi = image[y:y+h, x:x+w]
                ocr_text, barcodes = self._analyze_roi(roi)
                
                detections.append({
                    "type": "label_template",
                    "class": "detected_label",
                    "confidence": det['confidence'],
                    "bbox": [x, y, w, h],
                    "extracted_text": ocr_text,
                    "barcodes": barcodes
                })
        
        else:
            # Fallback: Run OCR/Barcode on full image if no models/templates
            logger.warning("No model or template loaded. Scanning full image.")
            ocr_text, barcodes = self._analyze_roi(image)
            detections.append({
                "type": "full_image_scan",
                "class": "general",
                "confidence": 1.0,
                "bbox": [0, 0, image.shape[1], image.shape[0]],
                "extracted_text": ocr_text,
                "barcodes": barcodes
            })

        return {
            "status": "success",
            "image_shape": image.shape,
            "detections": detections,
            "model_loaded": self.model is not None,
            "template_loaded": self.label_template is not None
        }

    def _analyze_roi(self, roi: np.ndarray) -> tuple[List[str], List[Dict]]:
        """Extract text and barcodes from a Region of Interest"""
        texts = []
        codes = []
        
        # 1. OCR
        try:
            result = self.reader.readtext(roi, detail=0)
            texts = result
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
        
        # 2. Barcode/QR Decode
        try:
            decoded_objects = pyzbar.decode(roi)
            for obj in decoded_objects:
                codes.append({
                    "type": obj.type,
                    "data": obj.data.decode('utf-8'),
                    "polygon": [(p.x, p.y) for p in obj.polygon]
                })
        except Exception as e:
            logger.error(f"Barcode decode failed: {str(e)}")
            
        return texts, codes

# Singleton instance
vision_engine = VisionEngine()
