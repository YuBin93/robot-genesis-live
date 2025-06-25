# api/generate_final_report.py
from http.server import BaseHTTPRequestHandler
import json, os, re
import google.generativeai as genai

# --- 配置与初始化 ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 辅助函数 ---
def extract_json_from_text(text):
    # ... (与 analyze_entity.py 中的版本相同)
    match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
    if match: return json.loads(match.group(1))
    start_index = text.find('{'); end_index = text.rfind('}')
    if start_index != -1 and end_index != -1: return json.loads(text[start_index : end_index + 1])
    raise json.JSONDecodeError("Could not find valid JSON.", text, 0)

# --- 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not API_KEY: raise ValueError("GEMINI_API_KEY not set.")
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            all_entity_data = json.loads(post_data)

            if not all_entity_data: raise ValueError("No entity data provided for final report.")

            print(f"--- Generating final report from {len(all_entity_data)} entities ---")
            context = json.dumps(all_entity_data, indent=2)

            prompt = f"""
            You are a senior market analyst. Based on the compiled JSON data for multiple robots, generate a comprehensive strategic analysis report.
            The report must be a single, valid JSON object following the structure I will define. Do not add any text outside this JSON object.
            The structure should include: "executive_summary", "competitive_landscape", and "market_trends_and_predictions".

            ### Compiled Data:
            {context}

            ### Strategic Report (JSON):
            """
            
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            response = model.generate_content(prompt, safety_settings=safety_settings)

            final_report_data = extract_json_from_text(response.text)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(final_report_data).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
