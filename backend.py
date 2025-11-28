import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from tools import object_detection_tool, semantic_segmentation_tool

# Load Env
load_dotenv()

# --- SETUP GROQ ---
api_key = "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"

if not api_key:
    # Default for local testing
    print("⚠️ Warning: GROQ_API_KEY not found in .env")

llm = ChatGroq(
    api_key=api_key,
    model_name="llama-3.3-70b-versatile",
    temperature=0.3
)

# FloodNet Class Mapping (ID -> Name)
SEG_CLASSES = {
    0: "Background", 
    1: "Building Flooded", 
    2: "Building Non-Flooded",
    3: "Road Flooded", 
    4: "Road Non-Flooded", 
    5: "Water",
    6: "Tree", 
    7: "Vehicle", 
    8: "Pool", 
    9: "Grass"
}

def get_image_data(image_path):
    """
    Runs Vision Tools and returns a comprehensive data dictionary.
    """
    print(f"🚀 Extracting Full Data from: {image_path}")
    
    # --- 1. RUN PERCEPTION TOOLS ---
    det_json = object_detection_tool.invoke(image_path)
    det_data = json.loads(det_json)
    
    seg_json = semantic_segmentation_tool.invoke(image_path)
    seg_data = json.loads(seg_json)
    
    # --- 2. PROCESS YOLO COUNTS (Objects) ---
    counts = det_data.get('counts', {})
    
    # Specific Counts
    flooded_bldgs = counts.get('Building Flooded', 0)
    safe_bldgs = counts.get('Building Non-Flooded', 0)
    vehicles = counts.get('Vehicle', 0)
    pools = counts.get('Pool', 0)
    
    total_buildings = flooded_bldgs + safe_bldgs
    if total_buildings > 0:
        bldg_damage_pct = (flooded_bldgs / total_buildings) * 100
    else:
        bldg_damage_pct = 0.0

    # --- 3. PROCESS SEGMENTATION (Terrain & Roads) ---
    pixel_counts = seg_data.get('pixel_counts', {})
    total_pixels = sum(pixel_counts.values()) if pixel_counts else 1
    
    # Calculate Area Percentages
    area_stats = {}
    for cls_id, cls_name in SEG_CLASSES.items():
        px_count = pixel_counts.get(str(cls_id), pixel_counts.get(cls_id, 0))
        pct = (px_count / total_pixels) * 100
        area_stats[cls_name] = round(pct, 2)

    # Road Specific Analysis
    road_flooded_area = area_stats.get("Road Flooded", 0)
    road_safe_area = area_stats.get("Road Non-Flooded", 0)
    total_road_area = road_flooded_area + road_safe_area
    
    if total_road_area > 0.1: 
        road_flood_severity = (road_flooded_area / total_road_area) * 100
    else:
        road_flood_severity = 0.0

    # --- 4. COMPILE FINAL DATA PACKET ---
    return {
        "flooded_bldgs": flooded_bldgs,
        "safe_bldgs": safe_bldgs,
        "vehicles": vehicles,
        "pools_count": pools,
        "bldg_damage_pct": bldg_damage_pct,
        "road_flood_severity_pct": road_flood_severity,
        "trees_pct": area_stats.get("Tree", 0),
        "grass_pct": area_stats.get("Grass", 0),
        "water_pct": area_stats.get("Water", 0),
        "map_path": seg_data.get('map_path', "")
    }

def chat_with_context(system_context, user_input):
    prompt = f"""
    SYSTEM INSTRUCTIONS:
    You are an advanced Disaster Response AI. You have access to precise sensor data from a drone.
    
    RESPONSE GUIDELINES:
    1. **VISUAL AWARENESS:** The user can see the "Visual Intel" panel on the left side of their screen. 
       - If they ask "Show me the map" or "Where is the flood?", say: "I have already visualized the flood extent for you. Please check the **AI Segmentation Mask** in the left panel."
    2. **DIRECT ANSWER:** Answer questions directly. Do not explain your logic.
    3. **BE SPECIFIC:** Use the provided counts (e.g., "5 vehicles") instead of vague terms ("some cars").
    4. **RELEVANCE:** Only mention road safety if relevant or if roads are totally blocked.
    5. **TONE:** Professional, concise, and helpful.

    SENSOR DATA CONTEXT:
    {system_context}

    USER QUESTION:
    {user_input}
    """
    
    response = llm.invoke(prompt)
    return response.content