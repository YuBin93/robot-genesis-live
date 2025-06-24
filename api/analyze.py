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
# 从Vercel的环境变量中安全地获取API Key
API_KEY = os.getenv("GEMINI_API_KEY")

# 只有在API_KEY存在时才配置SDK，避免在本地测试时因缺少KEY而崩溃
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    # 在部署环境（Vercel）中，如果找不到KEY，这是一个严重错误
    # 在日志中打印警告，以便于调试
    print("CRITICAL WARNING: GEMINI_API_KEY environment variable not found.")

# --- 2. Prompt构建函数 ---
# 这个函数负责构建给AI的指令，保持不变
def build_prompt(page_content, robot_name):
    """构建一个高质量的Prompt，指导Gemini完成任务"""
    
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
    Analyze the text from a webpage about the robot named '{robot_name}'.
    Your task is to extract key information and provide the output ONLY in a valid JSON format.
    The JSON object must strictly adhere to the structure shown below.
    If a piece of information is not available in the text, use "N/A" as the value.
    Do not include any introductory text, closing remarks, or markdown formatting like ```json.
    
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
# Vercel会自动找到这个handler类并执行它
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 检查API Key是否已配置，这是第一道防线
        if not API_KEY:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Server configuration error: The Gemini API Key is not set."}).encode())
            return

        # 解析URL，获取用户输入的机器人名称
        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]

        if not robot_name:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Please provide a robot name in the 'robot' parameter."}).encode())
            return
        
        try:
            # 步骤A: 智能搜索，找到最相关的网页
            print(f"🕵️ Searching for '{robot_name}'...")
            search_query = f"{robot_name} robot wikipedia"
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=1))
            
            if not results:
                raise ValueError(f"Could not find any relevant page for '{robot_name}'. Try a more specific name.")
            
            target_url = results[0]['href']
            print(f"🎯 Found URL: {target_url}")

            # 步骤B: 获取网页内容
            page_response = requests.get(target_url, headers={'User-Agent': 'Robot-Genesis-Live-Analyzer/1.1'})
            page_response.raise_for_status()
            soup = BeautifulSoup(page_response.content, 'html.parser')
            main_content = soup.find(id='mw-content-text') or soup.find('body')
            page_text = main_content.get_text(separator=' ', strip=True)

            # 步骤C: AI分析
            print(f"✨ Analyzing with Gemini...")
            prompt = build_prompt(page_text, robot_name)
            
            # --- 关键修改点：使用最新的、速度优化的模型 ---
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            gemini_response = model.generate_content(prompt, safety_settings=safety_settings)
            
            # 直接从响应中解析纯文本JSON
            robot_data = json.loads(gemini_response.text)
            
            # 步骤D: 成功返回结果给前端
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(robot_data).encode())

        except Exception as e:
            # 统一的、健壮的错误处理
            print(f"❌ An error occurred during the process: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode())
