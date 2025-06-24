# api/analyze.py

from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import google.generativeai as genai
from duckduckgo_search import DDGS
import re

# --- 1. 配置与初始化 (保持不变) ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("CRITICAL WARNING: GEMINI_API_KEY environment variable not found.")

# --- 2. 核心改变：全新的Prompt，用于初步情报分析 ---
def build_initial_analysis_prompt(search_results_text, robot_name):
    """
    构建一个全新的Prompt，指导AI对搜索结果进行初步分析和分类。
    """
    desired_json_structure = """
    {
      "robotInfo": {
        "name": "The most likely full official name of the robot.",
        "manufacturer": "The company or entity that creates the robot, inferred from the search results.",
        "type": "The category of the robot (e.g., Humanoid, Quadruped), inferred from the search results."
      },
      "summary": "A concise, one-paragraph summary of this robot's significance and key features, synthesized from the search result titles and snippets.",
      "sources": {
        "official": "The single most likely URL for the official product/company website.",
        "wikipedia": "The single most likely URL for the Wikipedia page.",
        "news": [
          {"title": "Title of a key news article", "url": "URL of the article"},
          {"title": "Another key news title", "url": "Another URL"}
        ],
        "videos": [
          {"title": "Title of a key video review", "url": "URL of the video"},
          {"title": "Another key video title", "url": "Another URL"}
        ]
      }
    }
    """
    prompt = f"""
    You are a world-class intelligence analyst. Your task is to analyze a list of web search results for the query '{robot_name}' and organize them into a structured intelligence briefing.
    Do not visit the URLs. Base your analysis solely on the provided search result text (titles and snippets).

    Your mission:
    1.  Deduce the robot's official name, manufacturer, and type from the collective information.
    2.  Write a compelling one-paragraph summary based on the gist of the search results.
    3.  Categorize the URLs. Identify the single best official website and Wikipedia page. Select up to 3 most relevant news articles and 2 most relevant videos.
    4.  Provide the output ONLY in a valid, minified JSON format, strictly adhering to the structure below. Do not add any comments or markdown.

    ### Desired JSON Structure:
    {desired_json_structure}

    ---
    ### Web Search Results:
    {search_results_text}
    ---

    ### Structured Intelligence Briefing (JSON):
    """
    return prompt

# --- 3. 智能JSON提取函数 (保持不变) ---
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

# --- 4. Serverless Function 主处理逻辑 (V2.0版) ---
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
            # 步骤A: 全网搜索，获取更丰富的原始结果
            print(f"🕵️ Performing a broad search for '{robot_name}'...")
            with DDGS() as ddgs:
                # 获取比之前更多的结果，给AI更多分析材料
                results = [r for r in ddgs.text(f"{robot_name} robot", max_results=10)]

            if not results:
                raise ValueError(f"Could not find any search results for '{robot_name}'.")

            # 将搜索结果格式化为纯文本，喂给AI
            search_results_text = "\n".join([f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---" for r in results])

            # 步骤B: AI进行初步情报分析
            print(f"🧠 Generating initial intelligence briefing with Gemini...")
            prompt = build_initial_analysis_prompt(search_results_text, robot_name)
            
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [ {"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"] ]
            
            gemini_response = model.generate_content(prompt, safety_settings=safety_settings)
            
            response_text_for_logging = gemini_response.text
            
            # 使用我们强大的JSON提取器
            intelligence_briefing = extract_json_from_text(response_text_for_logging)
            
            # 步骤C: 成功返回“情报包”JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(intelligence_briefing).encode())

        except Exception as e:
            # 统一的错误处理保持不变
            print(f"❌ An unhandled error occurred: {e}")
            if "response_text_for_logging" in locals() and response_text_for_logging:
                 print(f"--- Model's raw response was: ---\n{response_text_for_logging}\n---------------------------------")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode())
