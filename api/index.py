# api/index.py (Final Corrected Version - Includes All Helper Functions)

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

# --- 2. 必需的辅助函数 ---

def scrape_url(url):
    """抓取单个URL的精简文本内容"""
    try:
        print(f"  - Scraping: {url[:70]}...")
        response = requests.get(url, headers={'User-Agent': 'Robot-Genesis-Engine/4.1'}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # 移除所有脚本、样式、导航、页脚等噪音元素
        for element in soup(['script', 'style', 'nav', 'footer', 'header', '.mw-editsection', 'aside']):
            element.decompose()
        return soup.get_text(separator=' ', strip=True)[:4000] # 限制每个来源的文本长度
    except Exception as e:
        print(f"  - Failed to scrape {url}: {e}")
        return ""

def extract_json_from_text(text):
    """
    【关键函数】智能地从可能包含额外文本的字符串中提取JSON对象。
    """
    # 优先尝试寻找被Markdown代码块包裹的JSON
    match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            # 如果找到，就提取括号里的内容并解析
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            # 如果解析失败，继续尝试下一种方法
            pass

    # 如果没有找到Markdown块，就尝试寻找第一个'{'和最后一个'}'
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            potential_json = text[start_index : end_index + 1]
            return json.loads(potential_json)
    except json.JSONDecodeError:
        pass

    # 如果所有方法都失败了，就抛出一个明确的错误
    raise json.JSONDecodeError(f"Could not find a valid JSON object in the model's response.", text, 0)

def call_gemini(prompt, task_name):
    """一个集中的、健壮的Gemini API调用函数"""
    print(f"    - Calling Gemini for: {task_name}")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        
        # 【关键步骤】在这里使用我们的智能提取器，而不是直接用 response.text
        return extract_json_from_text(response.text)
        
    except Exception as e:
        print(f"    - Gemini call or JSON extraction for {task_name} failed: {e}")
        return {"error": f"AI task '{task_name}' failed.", "details": str(e)}


# --- 3. Serverless Function 主处理逻辑 ---
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
            # --- STAGE 1: INFORMATION GATHERING ---
            print(f"--- Stage 1: Gathering info for '{robot_name}' ---")
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(f"{robot_name} robot wikipedia specifications official website", max_results=7)]
            
            urls = [r['href'] for r in results]
            comprehensive_text = ""
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_url = {executor.submit(scrape_url, url): url for url in urls}
                for future in as_completed(future_to_url):
                    comprehensive_text += future.result() + "\n\n"

            if not comprehensive_text.strip():
                raise ValueError("Failed to gather any content for analysis.")
            
            # --- STAGE 2: TASK CHAIN EXECUTION ---
            print(f"--- Stage 2: Executing Analysis Task Chain ---")
            
            t1_prompt = f"Based on the provided text about '{robot_name}', analyze its technical architecture (Perception, Control, Locomotion). List the key functional components for each system. Output ONLY as a JSON object like this: {{\"perception_components\": [...], \"control_components\": [...], \"locomotion_components\": [...]}}.\n\nText: {comprehensive_text}"
            t1_output = call_gemini(t1_prompt, "T1_Tech_Architecture")
            
            t2_prompt = f"Given the text and these functional components: {json.dumps(t1_output)}. Map each function to specific hardware modules (e.g., 'object recognition' -> 'RGB cameras'). Output ONLY as a JSON object like this: {{\"hardware_mappings\": [{{\"function\": \"...\", \"hardware\": \"...\", \"purpose\": \"...\"}}]}}.\n\nText: {comprehensive_text}"
            t2_output = call_gemini(t2_prompt, "T2_Hardware_Mapping")

            t3_prompt = f"For each hardware module: {json.dumps(t2_output)}. Search the text for potential suppliers. If none are mentioned, list market leaders for that hardware. Output ONLY as a JSON object like this: {{\"supplier_mappings\": [{{\"hardware\": \"...\", \"suppliers\": [{\"name\": \"...\", \"country\": \"...\"}]}}]}}.\n\nText: {comprehensive_text}"
            t3_output = call_gemini(t3_prompt, "T3_Supplier_Matching")
            
            t4_prompt = f"Based on all the text, analyze the market landscape for humanoid robots like '{robot_name}'. Discuss market share, leaders, and challengers. Output ONLY as a JSON object with a single key 'market_analysis_summary'.\n\nText: {comprehensive_text}"
            t4_output = call_gemini(t4_prompt, "T4_Market_Analysis")

            t5_prompt = f"Synthesize the data from T1, T2, and T3 to create nodes and links for a Sankey diagram showing the flow: Function -> Hardware -> Supplier. Output ONLY as a JSON object like this: {{\"nodes\": [{{\"id\":\"...\"}}], \"links\": [{{\"source\":\"...\",\"target\":\"...\",\"value\":10}}]}}.\n\nData: T1={json.dumps(t1_output)}, T2={json.dumps(t2_output)}, T3={json.dumps(t3_output)}"
            t5_output = call_gemini(t5_prompt, "T5_Sankey_Data")

            # --- STAGE 3: AGGREGATE FINAL REPORT ---
            print("--- Stage 3: Aggregating Final Report ---")
            final_report = {
                "report_metadata": { "robot_name": robot_name, "generated_at": datetime.utcnow().isoformat() + "Z", "status": "Success" },
                "task_outputs": { "T1_tech_architecture": t1_output, "T2_hardware_mapping": t2_output, "T3_supplier_mapping": t3_output, "T4_market_analysis": t4_output, "T5_sankey_data": t5_output }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(final_report, indent=2).encode())

        except Exception as e:
            print(f"❌ Top-level error in V4 report generation: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Failed to generate the full report.", "details": str(e)}).encode())
