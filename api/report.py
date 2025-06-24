# api/report.py (V3.3 - Final, Rigorously Checked Version)

from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from duckduckgo_search import DDGS
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 1. CONFIGURATION & INITIALIZATION ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. HELPER FUNCTIONS ---
def scrape_url(url):
    try:
        print(f"  - Scraping: {url}")
        response = requests.get(url, headers={'User-Agent': 'Robot-Genesis-Report-Engine/3.3'}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        body = soup.find('body')
        if body:
            for element in body(['script', 'style', 'nav', 'footer', '.mw-editsection']):
                element.decompose()
            return body.get_text(separator=' ', strip=True)[:3000]
        return ""
    except Exception as e:
        print(f"  - Failed to scrape {url}: {e}")
        return None # Return None on failure to distinguish from empty string

def extract_json_from_text(text):
    match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except json.JSONDecodeError: pass
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return json.loads(text[start_index : end_index + 1])
    except json.JSONDecodeError: pass
    raise json.JSONDecodeError("Could not find a valid JSON object in the model's response.", text, 0)

def sanitize_text(text: str) -> str:
    if not text: return ""
    cleaned_text = re.sub(r'[^\w\s.,!?"\'\-\(\)\[\]\{\}:;%\$#@\u00C0-\u017F\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+', ' ', text)
    return re.sub(r'\s+', ' ', cleaned_text).strip()

# --- 3. PROMPT ENGINEERING ---
def build_final_fused_report_prompt(compiled_data_text):
    # This is the master prompt for the final report.
    return f"""
    You are a world-class senior analyst... (The full V3.1 prompt text here)
    ### Compiled Data from Multiple Sources:
    {compiled_data_text}
    ### Complete Strategic Report (JSON):
    """

# --- 4. CORE LOGIC CLASS ---
class handler(BaseHTTPRequestHandler):
    
    def gather_info_for_entity(self, entity):
        """Gathers and scrapes information for a single entity."""
        entity_name = entity["name"]
        print(f"  - Gathering for: {entity_name}")
        
        all_scraped_text = ""
        urls = []
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(f"{entity_name} robot {entity.get('manufacturer', '')}", max_results=4)]
            
            if not results: return entity_name, "", []
            
            urls = [r['href'] for r in results]
            
            scraped_texts = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_url = {executor.submit(scrape_url, url): url for url in urls}
                for future in as_completed(future_to_url):
                    result = future.result()
                    if result:
                        scraped_texts.append(result)
            
            all_scraped_text = " ".join(scraped_texts)
        except Exception as e:
            print(f"  - Error in gather_info_for_entity for {entity_name}: {e}")
            
        return entity_name, sanitize_text(all_scraped_text), urls

    def do_GET(self):
        if not API_KEY:
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Server configuration error: Gemini API Key is not set."}).encode())
            return

        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]

        if not robot_name:
            self.send_response(400); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Please provide a robot name."}).encode())
            return
        
        try:
            # === STAGE 1: IDENTIFY ENTITIES ===
            print(f"--- Stage 1: Identifying Entities for '{robot_name}' ---")
            entities = [{"name": robot_name, "manufacturer": ""}]
            
            # Simplified competitor logic for stability
            robot_name_lower = robot_name.lower()
            if "figure" in robot_name_lower:
                entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            elif "optimus" in robot_name_lower:
                entities.extend([{"name": "Figure 02", "manufacturer": "Figure AI"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            else: # Default competitors
                entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Figure 02", "manufacturer": "Figure AI"}])

            # === STAGE 2: PARALLEL INFORMATION GATHERING ===
            print(f"--- Stage 2: Parallel Information Gathering for {len(entities)} entities ---")
            
            # CRITICAL FIX: Ensure these dictionaries are defined in the correct scope.
            compiled_data = {}
            source_urls = {}
            
            with ThreadPoolExecutor(max_workers=len(entities)) as executor:
                future_to_entity = {executor.submit(self.gather_info_for_entity, entity): entity for entity in entities}
                for future in as_completed(future_to_entity):
                    entity = future_to_entity[future]
                    try:
                        entity_name, entity_text, entity_urls = future.result()
                        if entity_text:
                            compiled_data[entity_name] = entity_text
                            source_urls[entity_name] = entity_urls
                    except Exception as e:
                        print(f"  - Failed to process result for {entity['name']}: {e}")

            if not compiled_data:
                raise ValueError("Failed to gather sufficient information for any entity.")

            # === STAGE 3: GENERATE FINAL REPORT ===
            print("--- Stage 3: Generating Final Strategic Report ---")
            compiled_data_text = "\n\n".join([f"--- Data for {name} ---\n{text}" for name, text in compiled_data.items()])
            
            final_prompt = build_final_fused_report_prompt(compiled_data_text) # Re-inserting the full prompt here for self-containment
            final_prompt = f"""
            You are a world-class senior analyst, with dual expertise in robotics engineering and market strategy.
            Your mission is to generate a deeply researched, multi-layered strategic report based on the compiled data for several robots.
            The report must be a single, valid JSON object.

            The process is twofold:
            1.  **Bottom-up Technical Teardown**: For each robot, perform a detailed technical teardown, identifying its architecture, key components, and potential suppliers.
            2.  **Top-down Strategic Synthesis**: Based on the teardown data, perform a competitive analysis and identify market trends.

            The final JSON output MUST strictly follow this nested structure:
            {{
              "executive_summary": "A high-level summary of the competitive landscape and key findings.",
              "competitive_landscape": [
                {{
                  "robot_name": "Name of the first robot", "manufacturer": "Its manufacturer",
                  "technical_teardown": {{
                    "perception_system": {{ "key_components": ["List detailed components"], "potential_suppliers": ["List potential suppliers"] }},
                    "locomotion_system": {{ "key_components": ["..."], "potential_suppliers": ["..."] }},
                    "control_ai_system": {{ "key_components": ["..."], "potential_suppliers": ["..."] }}
                  }},
                  "strategic_analysis": {{
                    "strengths": ["List strengths derived from the teardown, e.g., 'Advanced perception suite from NVIDIA.'"],
                    "weaknesses": ["List weaknesses, e.g., 'Reliance on a single supplier for core AI.'"],
                    "market_position": "Describe its market positioning."
                  }}
                }}
              ],
              "market_trends_and_predictions": {{
                "key_technology_trends": ["Identify common tech trends observed from all teardowns."],
                "supply_chain_map": ["Identify common key suppliers across all robots and what this implies."],
                "future_outlook": "Provide a forward-looking prediction for the market."
              }},
              "data_confidence": {{
                "assessment": "Briefly assess the quality and completeness of the source data.",
                "identified_gaps": ["List key information that is still missing across all robots."]
              }}
            }}

            ### Compiled Data from Multiple Sources:
            {compiled_data_text}

            ### Complete Strategic Report (JSON):
            """
            
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [
                {"category": c, "threshold": "BLOCK_NONE"} for c in 
                ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
            ]
            final_response = model.generate_content(final_prompt, safety_settings=safety_settings)
            
            report_data = extract_json_from_text(final_response.text)
            report_data["_source_urls"] = source_urls

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(report_data).encode())

        except Exception as e:
            print(f"❌ Top-level error in report generation: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode())
