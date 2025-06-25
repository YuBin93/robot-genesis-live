# api/index.py (V5.0 - Function Calling Engine)

from http.server import BaseHTTPRequestHandler
import json, os, re
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# --- 1. CONFIG & INIT ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. HELPER FUNCTIONS ---
def professional_search(query):
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    print(f"  - Pro Search: '{query}'")
    if not SERPER_API_KEY: raise ValueError("SERPER_API_KEY not set.")
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": 7})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=payload, timeout=15)
    response.raise_for_status()
    return response.json()

# --- 3. 【全新】定义我们的“工具”/“函数” ---
robot_report_tool = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="submit_robot_report",
            description="Submits a comprehensive strategic analysis report for a given robot and its competitors.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "executive_summary": genai.protos.Schema(type=genai.protos.Type.STRING, description="A high-level summary of the current humanoid robot landscape and the main robot's position within it."),
                    "competitive_landscape": genai.protos.Schema(
                        type=genai.protos.Type.ARRAY,
                        description="An array of objects, each analyzing a competitor.",
                        items=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "robot": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "strengths": genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING)),
                                "weaknesses": genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING)),
                                "strategic_focus": genai.protos.Schema(type=genai.protos.Type.STRING)
                            }
                        )
                    ),
                    "market_trends_and_predictions": genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "key_technology_trends": genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING)),
                            "supply_chain_insights": genai.protos.Schema(type=genai.protos.Type.STRING),
                            "future_outlook_prediction": genai.protos.Schema(type=genai.protos.Type.STRING)
                        }
                    )
                },
                required=["executive_summary", "competitive_landscape", "market_trends_and_predictions"]
            )
        )
    ]
)

# --- 4. 【全新】调用AI并强制使用我们的工具 ---
def call_gemini_with_tool(prompt, task_name):
    print(f"    - Calling Gemini with Tool for: {task_name}")
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            tools=[robot_report_tool]
        )
        safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        
        function_call = response.candidates[0].content.parts[0].function_call
        if function_call.name == "submit_robot_report":
            # 将proto Map转换成Python字典
            report_args = {key: value for key, value in function_call.args.items()}
            # 递归地将内部的proto对象也转换
            if 'competitive_landscape' in report_args:
                report_args['competitive_landscape'] = [dict(item) for item in report_args['competitive_landscape']]
                for competitor in report_args['competitive_landscape']:
                    if 'strengths' in competitor: competitor['strengths'] = list(competitor['strengths'])
                    if 'weaknesses' in competitor: competitor['weaknesses'] = list(competitor['weaknesses'])
            if 'market_trends_and_predictions' in report_args:
                report_args['market_trends_and_predictions'] = dict(report_args['market_trends_and_predictions'])
                if 'key_technology_trends' in report_args['market_trends_and_predictions']:
                    report_args['market_trends_and_predictions']['key_technology_trends'] = list(report_args['market_trends_and_predictions']['key_technology_trends'])

            return report_args
        else:
            raise ValueError("AI did not call the expected function 'submit_robot_report'.")
    except Exception as e:
        print(f"    - Gemini tool call for {task_name} failed: {e}")
        return {"error": f"AI task '{task_name}' failed.", "details": str(e)}

# --- 5. SERVERLESS HANDLER ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not API_KEY:
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Server configuration error: API Key missing."}).encode())
            return
        
        query_components = parse_qs(urlparse(self.path).query)
        robot_name = query_components.get('robot', [None])[0]
        if not robot_name:
            self.send_response(400); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Please provide a robot name."}).encode())
            return
        
        try:
            print(f"--- V5.0 Engine Start for '{robot_name}' ---")
            
            print("--- Stage 1: Entity Recognition & Context Gathering ---")
            entities = [{"name": robot_name, "manufacturer": ""}]
            # ... (竞品逻辑保持不变)
            if "figure" in robot_name.lower(): entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            elif "optimus" in robot_name.lower(): entities.extend([{"name": "Figure 02", "manufacturer": "Figure AI"}, {"name": "Atlas", "manufacturer": "Boston Dynamics"}])
            else: entities.extend([{"name": "Optimus", "manufacturer": "Tesla"}, {"name": "Figure 02", "manufacturer": "Figure AI"}])
            
            search_queries = [f"{e['name']} {e.get('manufacturer','')} robot technical specifications news" for e in entities]
            comprehensive_text = ""
            with ThreadPoolExecutor(max_workers=len(search_queries)) as executor:
                future_to_query = {executor.submit(professional_search, q): q for q in search_queries}
                for future in as_completed(future_to_query):
                    try:
                        search_results = future.result()
                        comprehensive_text += f"\n\n--- Search Results for '{future_to_query[future]}' ---\n"
                        comprehensive_text += "\n".join([f"Title: {r.get('title', '')}\nSnippet: {r.get('snippet', '')}" for r in search_results.get('organic', [])])
                    except Exception as e:
                        print(f"  - Search query failed: {e}")
            
            if not comprehensive_text.strip(): raise ValueError("Professional search failed to gather any content.")

            print(f"--- Stage 2: Final Analysis via Function Calling ---")
            final_prompt = f"Please analyze the following compiled data about several robots, with a primary focus on '{robot_name}'. Then, submit your complete analysis by calling the 'submit_robot_report' tool with all the required arguments filled out.\n\n### Compiled Data:\n{comprehensive_text}"
            
            report_data = call_gemini_with_tool(final_prompt, "Final_Report_Generation")

            final_report = {
                "report_metadata": { "robot_name": robot_name, "generated_at": datetime.utcnow().isoformat() + "Z", "status": "Success" },
                "report_content": report_data 
            }
            
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(final_report, indent=2).encode())
        except Exception as e:
            print(f"❌ Top-level error in V5 report generation: {e}")
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Failed to generate the full report.", "details": str(e)}).encode())
