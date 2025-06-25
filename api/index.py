# api/index.py (V5.0 - Function Calling Engine)

from http.server import BaseHTTPRequestHandler
import json, os, re
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# --- 1. CONFIG & INIT ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. HELPER FUNCTIONS (scrape_url 保持不变) ---
# ...

# --- 3. 【全新】定义我们的“工具”/“函数” ---
# 这就是我们希望AI填充的最终报告结构
robot_report_tool = {
    "name": "submit_robot_report",
    "description": "Submits a comprehensive strategic analysis report for a given robot.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "executive_summary": {
                "type": "STRING",
                "description": "A high-level summary of the current humanoid robot landscape and the main robot's position within it."
            },
            "competitive_landscape": {
                "type": "ARRAY",
                "description": "An array of objects, each analyzing a competitor.",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "robot": {"type": "STRING", "description": "Name of the robot."},
                        "strengths": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Key advantages of this robot."},
                        "weaknesses": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Potential disadvantages of this robot."},
                        "strategic_focus": {"type": "STRING", "description": "The primary market strategy of this robot."}
                    },
                    "required": ["robot", "strengths", "weaknesses", "strategic_focus"]
                }
            },
            "market_trends_and_predictions": {
                "type": "OBJECT",
                "properties": {
                    "key_technology_trends": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "supply_chain_insights": {"type": "STRING"},
                    "future_outlook_prediction": {"type": "STRING"}
                }
            },
            "data_discrepancies_and_gaps": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["executive_summary", "competitive_landscape", "market_trends_and_predictions"]
    }
}

# --- 4. 【全新】调用AI并强制使用我们的工具 ---
def call_gemini_with_tool(prompt, task_name):
    print(f"    - Calling Gemini with Tool for: {task_name}")
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            # 告诉模型它可以使用这个工具
            tools=[robot_report_tool]
        )
        
        # 发起调用
        response = model.generate_content(prompt)
        
        # --- 检查AI是否决定调用我们的工具 ---
        function_call = response.candidates[0].content.parts[0].function_call
        if function_call.name == "submit_robot_report":
            # 如果是，直接从参数中获取干净的JSON对象
            report_arguments = function_call.args
            # 将其转换为字典（如果它不是的话）
            return dict(report_arguments)
        else:
            raise ValueError("AI did not call the expected function 'submit_robot_report'.")

    except Exception as e:
        print(f"    - Gemini tool call for {task_name} failed: {e}")
        return {"error": f"AI task '{task_name}' failed.", "details": str(e)}

# --- 5. SERVERLESS HANDLER (现在调用新的AI函数) ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ... (前面的检查逻辑保持不变) ...
        try:
            # ... (信息采集逻辑保持不变) ...

            # --- 最终分析调用 (核心改变) ---
            print("--- Stage 3: Generating Final Strategic Report via Function Calling ---")
            
            final_prompt = f"""
            Please analyze the following compiled data about several robots, with a primary focus on '{robot_name}'.
            Then, submit your complete analysis by calling the 'submit_robot_report' tool with all the required arguments filled out.

            ### Compiled Data:
            {comprehensive_text}
            """
            
            # 调用我们全新的、基于工具的AI函数
            report_data = call_gemini_with_tool(final_prompt, "Final_Report_Generation")
            
            # 我们不再需要聚合了，因为返回的直接就是报告内容
            final_report = {
                "report_metadata": { "robot_name": robot_name, "generated_at": datetime.utcnow().isoformat() + "Z", "status": "Success" },
                # 我们不再有T1-T5，只有一个最终的、完整的分析结果
                "report_content": report_data 
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(final_report, indent=2).encode())

        except Exception as e:
            # ... (错误处理保持不变) ...
