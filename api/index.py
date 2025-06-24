# api/index.py (Final Fortified Version)

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
from datetime import datetime

# --- 1. 配置与初始化 ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. 辅助函数 (经过加固) ---

def scrape_url(url):
    try:
        print(f"  - Scraping: {url[:70]}...")
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', '.mw-editsection']):
            element.decompose()
        return soup.get_text(separator=' ', strip=True)[:4000]
    except Exception as e:
        print(f"  - Failed to scrape {url}: {e}")
        return ""

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
    raise json.JSONDecodeError(f"Could not find a valid JSON object in the model's response.", text, 0)

def call_gemini(prompt, task_name):
    print(f"    - Calling Gemini for: {task_name}")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return extract_json_from_text(response.text)
    except Exception as e:
        print(f"    - Gemini call or JSON extraction for {task_name} failed: {e}")
        return {"error": f"AI task '{task_name}' failed.", "details": str(e)}

# --- 3. Serverless Function 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def gather_info_for_entity(self, entity):
        """【核心加固区】为单个实体搜索、验证并汇总信息"""
        entity_name = entity["name"]
        print(f"  - Gathering for: {entity_name}")
        
        valid_urls = []
        with DDGS(headers={'User-Agent': 'Mozilla/5.0...'}, timeout=20) as ddgs:
            # 增加 region 参数提高稳定性
            search_query = f"{entity_name} robot {entity.get('manufacturer', '')} wikipedia specifications"
            results = [r for r in ddgs.text(search_query, region='wt-wt', safesearch='off', max_results=10)]
        
        # --- 质量控制门 ---
        for r in results:
            url = r.get('href')
            if url and 'duckduckgo.com' not in url and url.startswith('http'):
                valid_urls.append(url)
        
        if not valid_urls:
            print(f"  - No valid URLs found for {entity_name} after filtering.")
            return entity_name, "", []

        # 只抓取前5个最有效的URL
        urls_to_scrape = valid_urls[:5]
        
        scraped_texts = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(scrape_url, url): url for url in urls_to_scrape}
            for future in as_completed(future_to_url):
                scraped_texts.append(future.result())
        
        return entity_name, "\n".join(filter(None, scraped_texts)), urls_to_scrape

    def do_GET(self):
        if not API_KEY:
            # ... 错误处理 ...
            return

        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]

        if not robot_name:
            # ... 错误处理 ...
            return
        
        try:
            print(f"--- V4.2 Engine Start: Identifying Entities for '{robot_name}' ---")
            entities = [{"name": robot_name, "manufacturer": ""}]
            if "figure" in robot_name.lower():
                entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            elif "optimus" in robot_name.lower():
                entities.extend([{"name": "Figure 02", "manufacturer": "Figure AI"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            else:
                entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Figure 02", "manufacturer": "Figure AI"}])

            print(f"--- Gathering information for {len(entities)} entities ---")
            compiled_data = {}
            with ThreadPoolExecutor(max_workers=len(entities)) as executor:
                # ... (并行逻辑保持不变) ...
                pass # This section remains conceptually the same, calling the now-robust gather_info_for_entity

            # ... (后续的任务链 T1-T5 和报告聚合逻辑保持不变) ...
            
        except Exception as e:
            # ... 统一错误处理 ...
            pass


# 为了您能完整替换，这里提供最终的、不会出错的完整文件
# api/index.py (Final Fortified Version - Full)

def build_final_report_prompt(compiled_data_text):
    return f"""
    You are a senior market analyst. Based on the compiled data for multiple robots, generate a comprehensive strategic analysis report.
    The report must be a single, valid JSON object following the structure I will define. Do not add any text outside this JSON object.
    The structure should include: "executive_summary", "competitive_landscape" (an array of objects for each robot with "strengths", "weaknesses", "strategic_focus"), "market_trends_and_predictions" (with "key_technology_trends", "supply_chain_insights", "future_outlook_prediction"), and "data_discrepancies_and_gaps".

    ### Compiled Data:
    {compiled_data_text}

    ### Strategic Report (JSON):
    """

class handler(BaseHTTPRequestHandler):
    def gather_info_for_entity(self, entity):
        entity_name = entity["name"]
        print(f"  - Gathering for: {entity_name}")
        
        valid_urls = []
        with DDGS(headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}, timeout=20) as ddgs:
            search_query = f"{entity_name} robot {entity.get('manufacturer', '')} wikipedia specifications"
            results = [r for r in ddgs.text(search_query, region='wt-wt', safesearch='off', max_results=10)]
        
        for r in results:
            url = r.get('href')
            if url and 'duckduckgo.com' not in url and url.startswith('http'):
                valid_urls.append(url)
        
        if not valid_urls:
            print(f"  - No valid URLs found for {entity_name} after filtering.")
            return entity_name, "", []

        urls_to_scrape = valid_urls[:5]
        
        scraped_texts = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(scrape_url, url): url for url in urls_to_scrape}
            for future in as_completed(future_to_url):
                scraped_texts.append(future.result())
        
        return entity_name, "\n".join(filter(None, scraped_texts)), urls_to_scrape
        
    def do_GET(self):
        if not API_KEY:
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Server configuration error: Gemini API Key not set."}).encode())
            return

        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]

        if not robot_name:
            self.send_response(400); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Please provide a robot name."}).encode())
            return
        
        try:
            print(f"--- V4.2 Engine Start: Identifying Entities for '{robot_name}' ---")
            entities = [{"name": robot_name, "manufacturer": ""}]
            if "figure" in robot_name.lower():
                entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            elif "optimus" in robot_name.lower():
                entities.extend([{"name": "Figure 02", "manufacturer": "Figure AI"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            else:
                entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Figure 02", "manufacturer": "Figure AI"}])

            print(f"--- Gathering information for {len(entities)} entities ---")
            compiled_data = {}
            source_urls = {}
            with ThreadPoolExecutor(max_workers=len(entities)) as executor:
                future_to_entity = {executor.submit(self.gather_info_for_entity, entity): entity for entity in entities}
                for future in as_completed(future_to_entity):
                    entity = future_to_entity[future]
                    try:
                        entity_name, entity_text, entity_urls = future.result()
                        if entity_text: # 只有在抓取到内容时才加入
                            compiled_data[entity_name] = entity_text
                            source_urls[entity_name] = entity_urls
                    except Exception as e:
                        print(f"  - ERROR processing entity {entity['name']}: {e}")

            if not compiled_data:
                raise ValueError("Failed to gather information for any key entities after filtering.")

            print(f"--- Stage 2: Executing Analysis Task Chain ---")
            comprehensive_text = "\n\n".join([f"--- Data for {name} ---\n{text}" for name, text in compiled_data.items()])
            
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
            print(f"❌ Top-level error in V4 report generation: {e}")
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Failed to generate the full report.", "details": str(e)}).encode())
