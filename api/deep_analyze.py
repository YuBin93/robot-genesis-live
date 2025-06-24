# api/deep_analyze.py

from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 1. 配置与初始化 (与analyze.py类似) ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("CRITICAL WARNING: GEMINI_API_KEY environment variable not found.")

# --- 2. 网页抓取辅助函数 ---
def scrape_url(url):
    """抓取单个URL的文本内容"""
    try:
        print(f"  - Scraping: {url}")
        response = requests.get(url, headers={'User-Agent': 'Robot-Genesis-Deep-Dive/1.0'}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # 提取更干净的正文
        body = soup.find('body')
        if body:
            # 移除脚本和样式，减少噪音
            for element in body(['script', 'style']):
                element.decompose()
            return body.get_text(separator=' ', strip=True)
        return ""
    except Exception as e:
        print(f"  - Failed to scrape {url}: {e}")
        return ""

# --- 3. 深度分析Prompt构建函数 ---
def build_deep_analysis_prompt(comprehensive_text):
    """构建一个用于深度技术分析的Prompt"""
    desired_json_structure = """
    {
      "technical_summary": "A summary of the robot's key technical specifications and innovations based on all provided text.",
      "perception_system": {
        "components": ["List of all mentioned sensor types like 'RGB cameras', 'LiDAR', 'IMU', 'microphones'."],
        "suppliers_and_partners": ["List of companies involved, e.g., 'NVIDIA', 'OpenAI'."],
        "analysis": "A brief analysis of the perception system's capabilities."
      },
      "locomotion_system": {
        "components": ["List of mechanical parts like 'Actuators', 'degrees of freedom (DOF)', 'battery system'."],
        "suppliers_and_partners": ["List any mentioned hardware partners."],
        "analysis": "A brief analysis of the locomotion system's design and performance."
      },
      "control_and_ai_system": {
        "components": ["Mention of 'AI models', 'neural networks', 'computational hardware'."],
        "suppliers_and_partners": ["List key AI partners like 'OpenAI', 'Google'."],
        "analysis": "A brief analysis of the robot's AI brain and control strategy."
      }
    }
    """
    prompt = f"""
    You are a senior robotics engineer. Analyze the comprehensive text compiled from multiple sources about a specific robot.
    Your task is to perform a deep technical dive and structure your findings into a valid JSON object.
    Focus on identifying and analyzing the robot's core systems. Be detailed and specific.

    ### Desired JSON Structure:
    {desired_json_structure}

    ---
    ### Comprehensive Text from Multiple Sources:
    {comprehensive_text[:30000]}
    ---

    ### Deep Technical Analysis (JSON Output):
    """
    return prompt

# --- 4. 智能JSON提取函数 (保持不变) ---
def extract_json_from_text(text):
    # ... (与上一版完全相同，为了简洁省略) ...
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

# --- 5. Serverless Function 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not API_KEY:
            # ... (错误处理) ...
            return
        
        try:
            # 步骤A: 获取前端发送过来的URL列表
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)
            urls = body.get('urls', [])

            if not urls:
                raise ValueError("No URLs provided for deep analysis.")
            
            # 步骤B: 并发抓取所有URL的内容
            print(f"🚀 Starting deep dive analysis on {len(urls)} sources...")
            all_texts = []
            # 使用线程池并发抓取，提高效率
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_url = {executor.submit(scrape_url, url): url for url in urls}
                for future in as_completed(future_to_url):
                    all_texts.append(future.result())
            
            comprehensive_text = "\n\n--- NEW SOURCE ---\n\n".join(filter(None, all_texts))
            
            if not comprehensive_text.strip():
                raise ValueError("Could not scrape any content from the provided URLs.")

            # 步骤C: AI进行深度分析
            print("🧠 Performing deep analysis with Gemini...")
            prompt = build_deep_analysis_prompt(comprehensive_text)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [ {"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"] ]
            gemini_response = model.generate_content(prompt, safety_settings=safety_settings)
            
            deep_analysis_data = extract_json_from_text(gemini_response.text)

            # 步骤D: 成功返回深度分析结果
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(deep_analysis_data).encode())

        except Exception as e:
            # ... (错误处理) ...
            print(f"❌ An error occurred during deep analysis: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode())
