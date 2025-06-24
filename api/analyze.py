# api/analyze.py

from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from duckduckgo_search import DDGS
import re # 引入正则表达式库

# --- 1. 配置与初始化 ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("CRITICAL WARNING: GEMINI_API_KEY environment variable not found.")

# --- 2. Prompt构建函数 ---
def build_prompt(page_content, robot_name):
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

# --- 3. 新增一个辅助函数：智能提取JSON ---
def extract_json_from_text(text):
    """
    使用多种方法从可能包含额外文本的字符串中提取JSON对象。
    """
    # 方法1：寻找被Markdown代码块包裹的JSON
    # 这会寻找 ```json ... ``` 这样的结构
    match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass # 如果失败，就继续尝试下一种方法

    # 方法2：寻找第一个 '{' 和最后一个 '}'
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            potential_json = text[start_index : end_index + 1]
            return json.loads(potential_json)
    except json.JSONDecodeError:
        pass

    # 如果所有方法都失败了，就抛出异常
    raise json.JSONDecodeError("Could not find a valid JSON object in the model's response.", text, 0)

# --- 4. Serverless Function 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not API_KEY:
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Server configuration error: The Gemini API Key is not set."}).encode())
            return

        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]

        if not robot_name:
            self.send_response(400); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Please provide a robot name."}).encode())
            return
        
        response_text_for_logging = ""
        try:
            print(f"🕵️ Searching for '{robot_name}'...")
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(f"{robot_name} robot wikipedia", max_results=3)]

            if not results: raise ValueError(f"Could not find any search results for '{robot_name}'.")

            target_url = next((r['href'] for r in results if 'wikipedia.org' in r['href']), results[0]['href'])
            print(f"🎯 Best URL found: {target_url}")

            page_response = requests.get(target_url, headers={'User-Agent': 'Robot-Genesis-Live-Analyzer/1.3'}, timeout=10)
            page_response.raise_for_status()
            soup = BeautifulSoup(page_response.content, 'html.parser')
            page_text = (soup.find(id='mw-content-text') or soup.find('body')).get_text(separator=' ', strip=True)

            print(f"✨ Analyzing with Gemini...")
            prompt = build_prompt(page_text, robot_name)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [ {"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"] ]
            
            gemini_response = model.generate_content(prompt, safety_settings=safety_settings)
            
            response_text_for_logging = gemini_response.text
            
            robot_data = extract_json_from_text(response_text_for_logging)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(robot_data).encode())

        except json.JSONDecodeError:
            print(f"❌ JSONDecodeError: Could not extract valid JSON. Model's raw response was: '{response_text_for_logging}'")
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "The AI model's response was not in the expected format. Please try again."}).encode())
        except Exception as e:
            print(f"❌ An unhandled error occurred: {e}")
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode())
