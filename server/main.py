import uvicorn
import re
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from neo4j import GraphDatabase
from contextlib import asynccontextmanager
from lib.fuzzy_matching import load_data_from_neo4j, hybrid_scorer_07_03, find_top_nodes_in_memory, find_best_node_text
from lib.allergens_detection import check_graph_connection
from lib.clean_string import clean_string


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌1. SYSTEM CONFIGURATION                  ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

load_dotenv()

# ═════════════ Configuration ═════════════

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")

NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
AUTH = (NEO4J_USER, NEO4J_PASSWORD) 

driver = GraphDatabase.driver(URI, auth=AUTH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    try:
        load_data_from_neo4j(driver)
    except Exception as e:
        print(f"Error when loading neo4j data: {e}")
    
    yield
    
    # --- SHUTDOWN ---
    print("Server is shutting down...")
    driver.close()
app = FastAPI(title="Food Allergy Detection API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow every access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ═══════════════════════════════════════════════

FOOD_CACHE = {}
FOOD_NAMES_LIST = []

# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌2. DATA INPUT/OUTPUT DEFINITION          ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

# App Request Data (Input)
class AllergyRequest(BaseModel):
    user_allergens: List[str]      # Ex: ["milk", "shrimp"]
    scanned_ingredients: List[str] # Ex: ["whey protein", "salt"]

# Warning detail
class WarningDetail(BaseModel):
    scanned_item: str    
    allergen_source: str 
    reason: str       

# Server Response Data (Output)
class AllergyResponseDebug(BaseModel):
    is_safe: bool              
    warnings: List[WarningDetail]  
    debug_mapping: Optional[dict] = None 

class AllergyResponse(BaseModel):
    mapped_scanned_allergies_label: List[str]
    mapped_user_allergies_label: List[str]
    ingredients_allergies: List[str]


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌3. API ENDPOINT (COMMUNICATE GATE)       ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

@app.post("/debug/check", response_model=AllergyResponseDebug)
async def check_allergy(request: AllergyRequest):
    print(f"\n📩 Request: Scan={request.scanned_ingredients} | User={request.user_allergens}")
    
    warnings = []
    debug_info = {}
    mapped_user_allergies_label = []
    user_allergen_map = {}


    for item in request.user_allergens:
        clean_item = clean_string(item)
        node = find_best_node_text(clean_item)
        if node:
            node_label = node["label"]
            mapped_user_allergies_label.append(node_label)
            print(f"   Mapped User Allergen: '{item}' -> '{node_label}'")
    

    if not mapped_user_allergies_label:
         return {"is_safe": True, "warnings": [], "debug_mapping": {}}


    for item in request.scanned_ingredients:
        clean_item = clean_string(item)
        node = find_best_node_text(clean_item)
        if not node:
            continue
        node_label = node["label"]
        print(f"   Mapped Scanned Ingredient: '{item}' -> '{node_label}'")
        debug_info[item] = node_label

        conflict_allergen_label = check_graph_connection(node_label, mapped_user_allergies_label, driver)
        if conflict_allergen_label:
            print(f"   🚨 ALERT: {item} <--> {conflict_allergen_label}")
            reason_msg = f"Product contains '{node_label}', related to '{conflict_allergen_label}'"
            warnings.append({
                "scanned_item": item,
                "allergen_source": conflict_allergen_label, 
                "reason": reason_msg
            })

    is_safe = len(warnings) == 0

    return {
        "is_safe": is_safe,
        "warnings": warnings,
        "debug_mapping": debug_info
    }

@app.post("/check", response_model=AllergyResponse)
async def check_allergy(request: AllergyRequest):
    print(f"\n📩 Request: Scan={request.scanned_ingredients} | User={request.user_allergens}")

    mapped_scanned_ingredients_label = []
    mapped_user_allergies_label = []
    ingredients_allergies = []

    # Mapping User Allergen List
    for item in request.user_allergens:
        clean_item = clean_string(item)
        node = find_best_node_text(clean_item)
        if node:
            node_label = node["label"]
            mapped_user_allergies_label.append(node_label)
        else:
            mapped_user_allergies_label.append("")

    # Mapping Scanned Ingredient List
    for item in request.scanned_ingredients:
        clean_item = clean_string(item)
        node = find_best_node_text(clean_item)
        if node:
            node_label = node["label"]
            mapped_scanned_ingredients_label.append(node_label)
            conflict_allergen_label = check_graph_connection(node_label, mapped_user_allergies_label, driver)
            if conflict_allergen_label:
                ingredients_allergies.append(conflict_allergen_label)
            else:
                ingredients_allergies.append("")

        else:
            mapped_scanned_ingredients_label.append("")
            ingredients_allergies.append("")
    return {
        "mapped_scanned_allergies_label": mapped_scanned_ingredients_label,
        "mapped_user_allergies_label": mapped_user_allergies_label,
        "ingredients_allergies": ingredients_allergies
    }

@app.get("/debug/node")
def debug_node(text: str):
    """Giúp bạn kiểm tra xem từ khóa map vào Node ID nào"""
    clean_text = clean_string(text)
    result = find_top_nodes_in_memory(clean_text)
    if len(result) > 0:
        node = result[0]
        print({
            "input_text": text,
            "mapped_node": node
        })
        return {
            "input_text": text,
            "mapped_node": node
        }
    else:
        print({
            "input_text": text,
            "mapped_node": None
        })
        return {
            "input_text": text,
            "mapped_node": None
        }

@app.get("/node")
def suggest_node(text: str):
    clean_text = clean_string(text)
    result = find_top_nodes_in_memory(clean_text, 5)
    response = []
    for item in result:
        response.append({
            "name": item["node"]["name"],
            "label": item["node"]["label"]
        })
    return {"suggest_nodes": response}
    

@app.get("/")
def health_check():
    return {"status": "running", "message": "Server is running!"}

# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌5. MAIN EXECUTION                        ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)