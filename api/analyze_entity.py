# api/generate_final_report.py (V5.2 - Pydantic Powered)

from http.server import BaseHTTPRequestHandler
import json, os
from urllib.parse import urlparse, parse_qs
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any

# --- 1. 配置与初始化 ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. 【全新】使用Pydantic定义我们严格的数据模型 ---

class CompetitorAnalysis(BaseModel):
    robot: str = Field(..., description="Name of the robot.")
    strengths: List[str] = Field(..., description="Key advantages of this robot.")
    weaknesses: List[str] = Field(..., description="Potential disadvantages of this robot.")
    strategic_focus: str = Field(..., description="The primary market strategy of this robot.")

class MarketTrends(BaseModel):
    key_technology_trends: List[str]
    supply_chain_insights: str
    future_outlook_prediction: str

class FinalReport(BaseModel):
    executive_summary: str = Field(..., description="A high-level summary of the current humanoid robot landscape.")
    competitive_landscape: List[CompetitorAnalysis]
    market_trends_and_predictions: MarketTrends

# --- 3. 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not API_KEY: raise ValueError("GEMINI_API_KEY not set.")
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            all_entity_data = json.loads(post_data)

            if not all_entity_data: raise ValueError("No entity data provided for final report.")

            print(f"--- V5.2 Engine: Generating final report for {len(all_entity_data)} entities ---")
            context = json.dumps(all_entity_data, indent=2)

            # 获取Pydantic模型的JSON Schema，作为给AI的“说明书”
            json_schema = FinalReport.model_json_schema()

            prompt = f"""
            You are a senior market analyst. Based on the compiled JSON data for multiple robots, generate a comprehensive strategic analysis report.
            Your output MUST be a single, valid JSON object that strictly conforms to the following JSON Schema. Do not add any text outside the JSON object.

            ### JSON Schema to follow:
            {json.dumps(json_schema, indent=2)}

            ### Compiled Data:
            {context}

            ### Strategic Report (JSON Output):
            """
            
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            
            # 请求JSON输出
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
                safety_settings=safety_settings
            )
            
            # --- 【全新】使用Pydantic进行验证和解析 ---
            try:
                # response.text里现在应该是更纯净的JSON字符串
                validated_report = FinalReport.model_validate_json(response.text)
                # 将验证后的Pydantic模型转换为字典，以便发送
                final_report_data = validated_report.model_dump()
            except ValidationError as e:
                # Pydantic的错误报告非常详细！
                print(f"❌ Pydantic Validation Error: {e}")
                # 将详细的验证错误信息返回给前端，便于调试
                raise ValueError(f"AI returned data that failed validation: {e}")


            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(final_report_data).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
