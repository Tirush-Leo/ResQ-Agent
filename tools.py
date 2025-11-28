import torch
from PIL import Image
import numpy as np
import json
import os
import cv2
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction
from langchain_core.tools import tool

# --- CONFIGURATION ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# FloodNet Color Palette
FLOODNET_PALETTE = np.array([
    [0, 0, 0],        # 0: Background
    [255, 0, 0],      # 1: Building Flooded (Red)
    [139, 69, 19],    # 2: Building Non-Flooded (Brown)
    [0, 0, 139],      # 3: Road Flooded (Dark Blue)
    [128, 128, 128],  # 4: Road Non-Flooded (Gray)
    [0, 191, 255],    # 5: Water (Light Blue)
    [34, 139, 34],    # 6: Tree (Green)
    [255, 215, 0],    # 7: Vehicle (Yellow)
    [0, 255, 255],    # 8: Pool (Cyan)
    [50, 205, 50]     # 9: Grass (Lime)
], dtype=np.uint8)

# --- LOAD MODELS ---
YOLO_PATH = os.path.join("models", "yolov8_floodnet.pt")
SEG_PATH = os.path.join("models", "segformer_custom")

print(f"Loading Models on {DEVICE}...")
try:
    detection_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8', model_path=YOLO_PATH, confidence_threshold=0.5, device=DEVICE
    )
    
    seg_processor = SegformerImageProcessor.from_pretrained("nvidia/mit-b0", do_reduce_labels=False)
    seg_model = SegformerForSemanticSegmentation.from_pretrained(SEG_PATH)
    seg_model.to(DEVICE)
    if DEVICE == "cuda": seg_model.half()
except Exception as e:
    print(f"⚠️ Model Load Error: {e}")
    detection_model = None
    seg_model = None

@tool
def object_detection_tool(image_path: str) -> str:
    """Detects objects (Flooded Building, Vehicle, etc.)."""
    try:
        if not os.path.exists(image_path): return json.dumps({"error": "File not found"})
        
        result = get_sliced_prediction(
            image_path, detection_model, slice_height=2000, slice_width=2000,
            overlap_height_ratio=0.05, overlap_width_ratio=0.05
        )

        detections = []
        counts = {}
        for obj in result.object_prediction_list:
            if obj.score.value < 0.5: continue
            label = obj.category.name
            detections.append({"label": label, "confidence": round(obj.score.value, 2)})
            counts[label] = counts.get(label, 0) + 1

        return json.dumps({"counts": counts, "detections": detections})
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def semantic_segmentation_tool(image_path: str) -> str:
    """
    Segments terrain.
    Returns JSON: {"map_path": "...", "pixel_counts": {...}}
    """
    try:
        image = Image.open(image_path).convert("RGB")
        orig_size = image.size
        
        # Resize for inference
        inputs = seg_processor(images=image.resize((768, 768), Image.BILINEAR), return_tensors="pt").to(DEVICE)
        if DEVICE == "cuda": inputs['pixel_values'] = inputs['pixel_values'].half()

        with torch.no_grad():
            outputs = seg_model(**inputs)
            
        upsampled = torch.nn.functional.interpolate(outputs.logits, size=(768, 768), mode='bilinear', align_corners=False)
        pred_seg = upsampled.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)
        
        # Resize mask to original size
        final_mask = cv2.resize(pred_seg, orig_size, interpolation=cv2.INTER_NEAREST)
        
        # --- NEW: CALCULATE PIXEL STATS ---
        # Count pixels for each class (0-9)
        unique, counts = np.unique(final_mask, return_counts=True)
        pixel_stats = dict(zip(unique.tolist(), counts.tolist()))
        
        # Save Colored Map
        color_mask = FLOODNET_PALETTE[final_mask]
        save_dir = "output_maps"
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.basename(image_path).replace('.jpg', '_seg_mask.png')
        out_path = os.path.join(save_dir, filename)
        Image.fromarray(color_mask).save(out_path)
        
        # Return BOTH path and stats
        return json.dumps({
            "map_path": out_path,
            "pixel_counts": pixel_stats # Dictionary of {class_id: count}
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})