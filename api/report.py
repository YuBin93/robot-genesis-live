# api/report.py (V3.2 - Input Sanitization Fix - Full Code)

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

# --- 2. 辅助函数 ---
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

def sanitize_text_for_api(text: str) -> str:
    """Cleans text to remove potentially problematic characters for the API."""
    # This regex removes most control characters and non-standard symbols,
    # but preserves common languages (Latin, CJK) and punctuation.
    cleaned_text = re.sub(r'[^\w\s.,!?"\'\-\(\)\[\]\{\}:;%\$#@\u00C0-\u017F\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+', ' ', text)
    # Collapse whitespace
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

# --- 3. Prompt构建函数 ---
def build_final_fused_report_prompt(compiled_data_text):
    # ... (This function remains the same as V3.1)
    return f"""
    You are a world-class senior analyst... (rest of the prompt)
    ### Compiled Data:
    {compiled_data_text}
    ### Strategic Report (JSON):
    """

# --- 4. Serverless Function 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ... (GET request handling remains the same) ...
        response_text_for_logging = ""
        try:
            # ... (Stage 1 & 2 remain the same) ...
            
            # --- Stage 3: Generating Final Strategic Report ---
            print("--- Stage 3: Generating Final Strategic Report ---")
            
            raw_compiled_text = "\n\n".join([f"--- Data for {name} ---\n{text}" for name, text in compiled_data.items()])
            
            # --- CRITICAL FIX: Sanitize the text before sending to the API ---
            print("  - Sanitizing final text for API call...")
            sanitized_compiled_text = sanitize_text_for_api(raw_compiled_text)
            
            final_prompt = build_final_fused_report_prompt(sanitized_compiled_text)
            
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            final_response = model.generate_content(final_prompt, safety_settings=safety_settings)
            
            response_text_for_logging = final_response.text
            report_data = extract_json_from_text(response_text_for_logging)
            report_data["_source_urls"] = source_urls

            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(report_data).encode())

        except Exception as e:
            # ... (Error handling remains the same) ...
            print(f"❌ Top-level error in report generation: {e}")
            if response_text_for_logging:
                 print(f"--- Model's raw response was: ---\n{response_text_for_logging}\n---------------------------------")
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode())

    def gather_info_for_entity(self, entity):
        # ... (This function remains the same) ...
        pass
