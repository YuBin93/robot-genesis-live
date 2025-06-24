# api/report.py (Final Corrected Version)

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

# --- 1. 配置与初始化 ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. 辅助函数 (scrape_url, extract_json_from_text) ---
# ... (这些函数保持不变，为简洁省略)

# --- 3. Prompt 构建函数 (build_competitor_id_prompt, etc.) ---
# ... (这些函数保持不变，为简洁省略)

# --- 4. Serverless Function 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ... (前面的GET请求处理逻辑保持不变) ...
        # ... (只展示被修改的部分) ...
        try:
            # ...
            # 3. 进行最终的关联性分析
            print("--- Stage 3: Generating Final Strategic Report ---")
            compiled_data_text = "\n\n".join([f"--- Data for {name} ---\n{text}" for name, text in compiled_data.items()])
            
            final_prompt = build_final_report_prompt(compiled_data_text)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            # --- 完整的、正确的 safety_settings 定义 ---
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            final_response = model.generate_content(final_prompt, safety_settings=safety_settings)
            
            report_data = extract_json_from_text(final_response.text)
            report_data["_source_urls"] = source_urls
            
            # 4. 成功返回最终报告
            # ...
        except Exception as e:
            # ...
            pass
            
    def gather_info_for_entity(self, entity):
        # ... (此函数保持不变) ...
        pass

# --- 为了您能完整替换，这里提供最终的、不会出错的完整文件 ---
# api/report.py (Final Corrected Version - Full)
def scrape_url(url):
    try:
        print(f"  - Scraping: {url}")
        response = requests.get(url, headers={'User-Agent': 'Robot-Genesis-Report-Engine/3.0'}, timeout=10)
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
    raise json.JSONDecodeError("Could not find a valid JSON object in the model's response.", text, 0)

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
            print(f"--- Stage 1: Identifying Entities for '{robot_name}' ---")
            entities = [{"name": robot_name, "manufacturer": ""}]
            
            if "figure" in robot_name.lower():
                entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            elif "optimus" in robot_name.lower():
                entities.extend([{"name": "Figure 02", "manufacturer": "Figure AI"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            else: # Default competitors
                entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Figure 02", "manufacturer": "Figure AI"}])

            print(f"--- Stage 2: Parallel Information Gathering for {len(entities)} entities ---")
            compiled_data = {}
            source_urls = {}
            with ThreadPoolExecutor(max_workers=len(entities)) as executor:
                future_to_entity = {executor.submit(self.gather_info_for_entity, entity): entity for entity in entities}
                for future in as_completed(future_to_entity):
                    entity = future_to_entity[future]
                    try:
                        entity_name, entity_text, entity_urls = future.result()
                        compiled_data[entity_name] = entity_text
                        source_urls[entity_name] = entity_urls
                    except Exception as e:
                        print(f"  - Failed to gather info for {entity['name']}: {e}")

            if not compiled_data:
                raise ValueError("Failed to gather information for any entity.")

            print("--- Stage 3: Generating Final Strategic Report ---")
            compiled_data_text = "\n\n".join([f"--- Data for {name} ---\n{text}" for name, text in compiled_data.items()])
            
            final_prompt = build_final_report_prompt(compiled_data_text)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
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
    
    def gather_info_for_entity(self, entity):
        entity_name = entity["name"]
        print(f"  - Gathering for: {entity_name}")
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(f"{entity_name} robot {entity.get('manufacturer', '')}", max_results=5)]
        
        urls = [r['href'] for r in results]
        
        scraped_texts = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(scrape_url, url): url for url in urls}
            for future in as_completed(future_to_url):
                scraped_texts.append(future.result())
        
        return entity_name, "\n".join(filter(None, scraped_texts)), urls
