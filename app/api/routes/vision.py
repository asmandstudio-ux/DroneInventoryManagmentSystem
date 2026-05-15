from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
from app.services.vision_engine import vision_engine
from app.api.deps import get_current_superuser
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/api/vision", tags=["AI Vision"])

@router.get("/status")
async def get_vision_status():
    """Check if YOLO model and Label Template are loaded"""
    return {
        "model_loaded": vision_engine.model is not None,
        "model_path": settings.VISION_MODEL_PATH,
        "template_loaded": vision_engine.label_template is not None,
        "template_path": settings.LABEL_TEMPLATE_PATH
    }

@router.post("/upload-weights")
async def upload_yolo_weights(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_superuser)
):
    """Upload custom trained YOLOv8 .pt weights"""
    if not file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="File must be a .pt (PyTorch) file")
    
    save_path = settings.VISION_MODEL_PATH
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Reload engine
        success = vision_engine.load_model(save_path)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to load model after upload")
            
        return {"message": "Weights uploaded and loaded successfully", "path": save_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-label-template")
async def upload_label_template(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_superuser)
):
    """Upload a reference label image for template matching"""
    allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail=f"File must be an image {allowed_extensions}")
    
    save_path = settings.LABEL_TEMPLATE_PATH
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Reload engine
        success = vision_engine.load_template(save_path)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to load template after upload")
            
        return {"message": "Template uploaded and loaded successfully", "path": save_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan")
async def scan_inventory_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_superuser) # Or appropriate role
):
    """
    Process an inventory image:
    1. Detects labels using YOLO or Template Matching
    2. Extracts Text (OCR)
    3. Decodes Barcodes/QR Codes
    """
    allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Invalid image format")
    
    # Save temp file
    temp_dir = settings.TEMP_DIR
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"scan_{file.filename}")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process
        result = vision_engine.process_image(temp_path)
        
        # Cleanup temp file (optional: move to S3 instead)
        # os.remove(temp_path) 
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
