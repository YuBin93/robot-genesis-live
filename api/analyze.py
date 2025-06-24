# api/analyze.py

from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- 1. 配置与初始化 (不变) ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("CRITICAL WARNING: GEMINI_API_KEY environment variable not found.")

# --- 2. 优化后的Prompt构建函数 (关键改动) ---
def build_prompt(page_content, robot_name):
    """
    优化后的Prompt，指导AI更智能地提取信息，并对找不到的信息进行合理推断。
    """
    desired_json_structure = """
    {
      "name": "Robot's full name, e.g., 'Tesla Optimus Gen 2'",
      "manufacturer": "The company that created the robot, e.g., 'Tesla, Inc.'",
      "type": "Type of robot, e.g., 'Humanoid'",
      "specs": {
        "Weight": "Weight of the robot, e.g., '57 kg (125 lb)'",
        "Payload": "Payload capacity, e.g., '20 kg (45 lb)'",
        "Speed": "Maximum speed, e.g., '8 km/h'"
      },
      "modules": {
        "Perception System": { "components": ["List of sensors like 'Cameras', 'IMU', 'Force Sensors'"], "suppliers": ["If known, list suppliers like 'Sony (for cameras)', 'Bosch (for IMU)'. If unknown, list potential industry leaders or 'In-house' if likely self-made."] },
        "Actuation/Locomotion": { "components": ["List of components like 'Custom Actuators', 'Electric Motors', 'Harmonic Drives'"], "suppliers": ["If known, list suppliers. If unknown, list 'In-house' or potential market leaders like 'Harmonic Drive AG'."] },
        "AI/Computing": { "components": ["The main computing chip, e.g., 'Custom SoC (System on a Chip)', 'NVIDIA Jetson'"], "suppliers": ["List the chip designer, e.g., 'Tesla', 'NVIDIA'."] }
      }
    }
    """
    prompt = f"""
    You are an expert robotics analyst. Your task is to analyze the following text about the robot named '{robot_name}' and extract key information into a structured JSON format.

    **Instructions:**
    1.  Provide the output ONLY in a valid JSON format, strictly adhering to the structure below.
    2.  If a specific piece of information (like Speed) is not mentioned, use "N/A".
    3.  **Crucially, for 'suppliers'**: If the text does not explicitly name suppliers, use your expert knowledge to infer likely scenarios. For major tech companies like Tesla, it's often 'In-house' or 'Custom'. For components like cameras or sensors, you can list major industry players as 'potential' suppliers. This adds value beyond simple extraction.
    4.  Do not include any introductory text, closing remarks, or markdown formatting like ```json.

    ### Desired JSON Structure with Examples:
    {desired_json_structure}

    ### Page Content to Analyze:
    ---
    {page_content[:20000]} 
    ---

    ### Extracted JSON Data:
    """
    return prompt

# --- 3. Serverless Function 主处理逻辑 (搜索策略微调) ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ... (前半部分检查API Key和参数的代码保持不变) ...
        if not API_KEY: # ...
            return
        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]
        if not robot_name: # ...
            return
        
        try:
            # 优化搜索策略：优先找维基，再找官方或权威新闻
            print(f"🕵️ Searching for '{robot_name}'...")
            # 构造更精确的搜索词
            search_queries = [
                f"{robot_name} robot wikipedia",
                f"{robot_name} official website specs",
                f"robot '{robot_name}' technical specifications"
            ]
            
            target_url = None
            with DDGS() as ddgs:
                for query in search_queries:
                    results = list(ddgs.text(query, max_results=1))
                    if results:
                        target_url = results[0]['href']
                        print(f"🎯 Found URL via query '{query}': {target_url}")
                        break
            
            if not target_url:
                raise ValueError(f"Could not find any relevant page for '{robot_name}'.")

            # ... (后续获取内容、AI分析、返回结果的代码保持不变) ...
            page_response = requests.get(target_url, headers={'User-Agent': 'Robot-Genesis-Live-Analyzer/1.2'})
            #...
            # The rest of the code is the same as the previous version.
            page_response.raise_for_status()
            soup = BeautifulSoup(page_response.content, 'html.parser')
            main_content = soup.find(id='mw-content-text') or soup.find('body')
            page_text = main_content.get_text(separator=' ', strip=True)

            print(f"✨ Analyzing with Gemini...")
            prompt = build_prompt(page_text, robot_name)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [ {"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"] ]
            gemini_response = model.generate_content(prompt, safety_settings=safety_settings)
            robot_data = json.loads(gemini_response.text)
            
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(robot_data).encode())

        except Exception as e:
            print(f"❌ An error occurred: {e}")
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode())
