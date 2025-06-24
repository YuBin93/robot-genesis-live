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
    print("WARNING: GEMINI_API_KEY environment variable not found.")

# --- 2. Prompt构建函数 ---
def build_prompt(page_content, robot_name):
    desired_json_structure = """
    {
      "name": "Robot's full name",
      "manufacturer": "The company that created the robot",
      "type": "Type of robot (e.g., Quadruped, Humanoid)",
      "specs": {
        "Weight": "Weight of the robot (e.g., 75 kg)",
        "Payload": "Payload capacity (e.g., 25 kg)",
        "Speed": "Maximum speed (e.g., 1.5 m/s)"
      },
      "modules": {
        "Perception": { "components": ["List of sensors like Cameras, LiDAR, IMU"], "suppliers": ["List of potential suppliers"] },
        "Locomotion": { "components": ["List of components like Actuators, Hydraulic systems"], "suppliers": ["List of potential suppliers"] }
      }
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
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Server configuration error: Gemini API Key not set."}).encode())
            return

        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]

        if not robot_name:
            self.send_response(400); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing 'robot' parameter"}).encode())
            return
        
        try:
            # 智能搜索
            print(f"🕵️ Searching for '{robot_name}'...")
            search_query = f"{robot_name} robot wikipedia"
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=1))
            if not results: raise ValueError("Could not find any relevant page.")
            target_url = results[0]['href']
            print(f"🎯 Found URL: {target_url}")

            # 获取内容
            page_response = requests.get(target_url, headers={'User-Agent': 'Robot-Genesis-Live-Analyzer/1.0'})
            page_response.raise_for_status()
            soup = BeautifulSoup(page_response.content, 'html.parser')
            page_text = (soup.find(id='mw-content-text') or soup.find('body')).get_text(separator=' ', strip=True)

            # AI分析
            print(f"✨ Analyzing with Gemini...")
            prompt = build_prompt(page_text, robot_name)
            model = genai.GenerativeModel('gemini-pro')
            safety_settings = [ {"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"] ]
            gemini_response = model.generate_content(prompt, safety_settings=safety_settings)
            
            robot_data = json.loads(gemini_response.text)
            
            # 成功返回
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(robot_data).encode())

        except Exception as e:
            # 统一错误处理
            print(f"❌ An error occurred: {e}")
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
