# api/index.py (V4.3 - FINAL VERSION)

from http.server import BaseHTTPRequestHandler
import json, os, re
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# --- 1. CONFIG & INIT ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- 2. HELPER FUNCTIONS ---
def professional_search(query):
    print(f"  - Pro Search: '{query}'")
    if not SERPER_API_KEY: raise ValueError("SERPER_API_KEY not set.")
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": 7})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=payload, timeout=15)
    response.raise_for_status()
    return response.json()

def extract_json_from_text(text):
    match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except json.JSONDecodeError: pass
    try:
        start_index = text.find('{'); end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return json.loads(text[start_index : end_index + 1])
    except json.JSONDecodeError: pass
    raise json.JSONDecodeError("Could not find valid JSON in model's response.", text, 0)

def call_gemini(prompt, task_name):
    print(f"    - Gemini Task: {task_name}")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return extract_json_from_text(response.text)
    except Exception as e:
        print(f"    - Gemini task '{task_name}' failed: {e}")
        return {"error": f"AI task '{task_name}' failed.", "details": str(e)}

# --- 3. MAIN HANDLER ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not GEMINI_API_KEY or not SERPER_API_KEY:
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Server configuration error: API Key missing."}).encode())
            return
        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]
        if not robot_name:
            self.send_response(400); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Please provide a robot name."}).encode())
            return
        
        try:
            print(f"--- V4.3 Engine Start for '{robot_name}' ---")
            
            print("--- Stage 1: Entity Recognition & Context Gathering ---")
            entities = [{"name": robot_name, "manufacturer": ""}]
            if "figure" in robot_name.lower(): entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            elif "optimus" in robot_name.lower(): entities.extend([{"name": "Figure 02", "manufacturer": "Figure AI"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            else: entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Figure 02", "manufacturer": "Figure AI"}])

            search_queries = [f"{e['name']} {e.get('manufacturer','')} robot technical specifications components" for e in entities]
            comprehensive_text = ""
            with ThreadPoolExecutor(max_workers=len(search_queries)) as executor:
                future_to_query = {executor.submit(professional_search, q): q for q in search_queries}
                for future in as_completed(future_to_query):
                    try:
                        search_results = future.result()
                        comprehensive_text += f"\n\n--- Search Results for '{future_to_query[future]}' ---\n"
                        comprehensive_text += "\n".join([f"Title: {r.get('title', '')}\nSnippet: {r.get('snippet', '')}" for r in search_results.get('organic', [])])
                    except Exception as e:
                        print(f"  - Search query failed: {e}")
            
            if not comprehensive_text.strip(): raise ValueError("Professional search failed to gather any content.")
            
            print(f"--- Stage 2: Executing Analysis Task Chain (Context length: {len(comprehensive_text)}) ---")
            t1_prompt = f"Based on the provided text about '{robot_name}', analyze its technical architecture (Perception, Control, Locomotion). List the key functional components for each system. Output ONLY as a JSON object like this: {{{{ \"perception_components\": [...], \"control_components\": [...], \"locomotion_components\": [...] }}}}.\n\nText: {comprehensive_text}"
            t1_output = call_gemini(t1_prompt, "T1_Tech_Architecture")
            t2_prompt = f"""Given the text and these functional components: {json.dumps(t1_output)}. Map each function to specific hardware modules (e.g., 'object recognition' -> 'RGB cameras'). Output ONLY as a JSON object like this: {{{{ "hardware_mappings": [{{ "function": "...", "hardware": "...", "purpose": "..." }}] }}}}.\n\nText: {comprehensive_text}"""
            t2_output = call_gemini(t2_prompt, "T2_Hardware_Mapping")
            t3_prompt = f"""For each hardware module: {json.dumps(t2_output)}. Search the text for potential suppliers. If none are mentioned, list market leaders for that hardware. Output ONLY as a JSON object like this: {{{{ "supplier_mappings": [{{ "hardware": "...", "suppliers": [{{ "name": "...", "country": "..." }}] }}] }}}}.\n\nText: {comprehensive_text}"""
            t3_output = call_gemini(t3_prompt, "T3_Supplier_Matching")
            t4_prompt = f"""Based on all the text, analyze the market landscape for humanoid robots like '{robot_name}'. Discuss market share, leaders, and challengers. Output ONLY as a JSON object with a single key 'market_analysis_summary'.\n\nText: {comprehensive_text}"""
            t4_output = call_gemini(t4_prompt, "T4_Market_Analysis")
            t5_prompt = f"""Synthesize the data from T1, T2, and T3 to create nodes and links for a Sankey diagram showing the flow: Function -> Hardware -> Supplier. Output ONLY as a JSON object like this: {{{{ "nodes": [{{ "id":"..." }}], "links": [{{ "source":"...", "target":"...", "value":10 }}] }}}}.\n\nData: T1={json.dumps(t1_output)}, T2={json.dumps(t2_output)}, T3={json.dumps(t3_output)}"""
            t5_output = call_gemini(t5_prompt, "T5_Sankey_Data")

            print("--- Stage 3: Aggregating Final Report ---")
            final_report = {
                "report_metadata": { "robot_name": robot_name, "generated_at": datetime.utcnow().isoformat() + "Z", "status": "Success" },
                "task_outputs": { "T1_tech_architecture": t1_output, "T2_hardware_mapping": t2_output, "T3_supplier_mapping": t3_output, "T4_market_analysis": t4_output, "T5_sankey_data": t5_output }
            }
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(final_report, indent=2).encode())
        except Exception as e:
            print(f"❌ Top-level error in V4.3 report generation: {e}")
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Failed to generate the full report.", "details": str(e)}).encode())
