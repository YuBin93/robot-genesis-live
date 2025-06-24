# api/analyze.py

from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- 1. 配置与初始化 ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("CRITICAL WARNING: GEMINI_API_KEY environment variable not found.")

# --- 2. Prompt构建函数 (保持不变) ---
def build_prompt(page_content, robot_name):
    # ... (这部分代码与之前完全相同，为了简洁省略) ...
    desired_json_structure = """
    {
      "name": "Robot's full name", "manufacturer": "The company that created the robot", "type": "Type of robot (e.g., Quadruped, Humanoid)",
      "specs": { "Weight": "Weight of the robot (e.g., 75 kg)", "Payload": "Payload capacity (e.g., 25 kg)", "Speed": "Maximum speed (e.g., 1.5 m/s)" },
      "modules": { "Perception": { "components": ["List of sensors like Cameras, LiDAR, IMU"], "suppliers": ["List of potential suppliers"] }, "Locomotion": { "components": ["List of components like Actuators, Hydraulic systems"], "suppliers": ["List of potential suppliers"] } }
    }
    """
    prompt = f"""
    Analyze the text from a webpage about the robot named '{robot_name}'. Your task is to extract key information and provide the output ONLY in a valid JSON format. The JSON object must strictly adhere to the structure shown below. If a piece of information is not available in the text, use "N/A" as the value. Do not include any introductory text, closing remarks, or markdown formatting like ```json.

    ### Desired JSON Structure:
    {desired_json_structure}
    ### Page Content to Analyze:
    ---
    {page_content[:20000]} 
    ---
    ### Extracted JSON Data:
    """
    return prompt

# --- 3. Serverless Function 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not API_KEY:
            # ... (错误处理与之前相同) ...
            return

        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]

        if not robot_name:
            # ... (错误处理与之前相同) ...
            return
        
        try:
            # 步骤A: 智能搜索 (修正逻辑)
            print(f"🕵️ Searching for '{robot_name}'...")
            search_query = f"{robot_name} robot wikipedia"
            
            # 使用DDGS上下文管理器确保正确关闭
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(search_query, max_results=3)] # 获取前3个结果以增加容错

            if not results:
                raise ValueError(f"Could not find any search results for '{robot_name}'.")
            
            # 优先选择包含wikipedia.org的链接
            target_url = None
            for result in results:
                if 'wikipedia.org' in result['href']:
                    target_url = result['href']
                    break
            
            # 如果没有维基百科链接，就用第一个结果
            if not target_url:
                target_url = results[0]['href']

            print(f"🎯 Best URL found: {target_url}")

            # 步骤B: 获取网页内容
            page_response = requests.get(target_url, headers={'User-Agent': 'Robot-Genesis-Live-Analyzer/1.2'}, timeout=10)
            page_response.raise_for_status()
            soup = BeautifulSoup(page_response.content, 'html.parser')
            page_text = (soup.find(id='mw-content-text') or soup.find('body')).get_text(separator=' ', strip=True)

            # 步骤C: AI分析 (增加健壮性)
            print(f"✨ Analyzing with Gemini...")
            prompt = build_prompt(page_text, robot_name)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [ {"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"] ]
            
            gemini_response = model.generate_content(prompt, safety_settings=safety_settings)
            
            # --- 关键修正点：在解析前检查返回内容 ---
            response_text = gemini_response.text.strip()
            if not response_text:
                # 如果模型返回空，这是一个可预见的错误
                raise ValueError("AI model returned an empty response. This might be due to content safety filters or an inability to analyze the page.")

            # 尝试解析JSON
            robot_data = json.loads(response_text)
            
            # 步骤D: 成功返回结果
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(robot_data).encode())

        except json.JSONDecodeError:
            # 专门处理JSON解析失败的错误
            print(f"❌ JSONDecodeError: AI model did not return a valid JSON. Response was: {response_text}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "The AI model's response was not in the expected format. Please try again."}).encode())
        except Exception as e:
            # 捕获所有其他错误
            print(f"❌ An unhandled error occurred: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode())
