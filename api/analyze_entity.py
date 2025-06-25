# api/analyze_entity.py (Correct, Caching-Enabled Version)

from http.server import BaseHTTPRequestHandler
import json, os, re, requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import google.generativeai as genai
from upstash_redis import Redis # 确保使用的是upstash-redis

# --- 1. 配置与初始化 ---
API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# 尝试从Vercel的环境变量中初始化Redis客户端
try:
    redis = Redis.from_env()
except Exception as e:
    print(f"Warning: Could not initialize Redis from env. Caching will be disabled. Error: {e}")
    redis = None

# --- 2. 辅助函数 ---
def professional_search(query):
    if not SERPER_API_KEY: raise ValueError("SERPER_API_KEY not set.")
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": 5})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=payload, timeout=15)
    response.raise_for_status()
    return response.json()

def extract_json_from_text(text):
    # 这个函数用于从可能包含额外文本的字符串中提取JSON
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

# --- 3. 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not API_KEY: raise ValueError("GEMINI_API_KEY not set.")
            robot_name_raw = parse_qs(urlparse(self.path).query).get('name', [None])[0]
            if not robot_name_raw: raise ValueError("'name' parameter is missing.")
            
            robot_name = robot_name_raw.strip().lower()
            cache_key = f"robot_entity_v2:{robot_name.replace(' ', '_')}" # 使用新版缓存键

            # --- 步骤A: 检查缓存 ---
            if redis:
                print(f"--- Analyzing entity: {robot_name} ---")
                print(f"  - Checking Upstash cache with key: {cache_key}")
                cached_data = redis.get(cache_key)
                if cached_data:
                    print("  - ✅ Cache HIT! Returning cached data.")
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(json.loads(cached_data)).encode('utf-8'))
                    return
                print("  - ❌ Cache MISS. Proceeding to live analysis.")
            
            # --- 步骤B: 如果缓存未命中，执行实时分析 ---
            search_results = professional_search(f"{robot_name} robot specifications")
            context = "\n".join([f"Title: {r.get('title', '')}\nSnippet: {r.get('snippet', '')}" for r in search_results.get('organic', [])])
            if not context.strip(): raise ValueError("Search returned no content.")

            prompt = f"""
            Based on the provided search results for '{robot_name}', extract key information.
            Output ONLY as a valid JSON object like this, with no extra text or markdown:
            {{
                "name": "Full official name", 
                "manufacturer": "The manufacturer", 
                "summary": "A one-sentence summary.", 
                "specs": {{ "Weight": "...", "Payload": "..." }}
            }}
            
            ### Search Results:
            {context}

            ### JSON Output:
            """
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            
            # 请求JSON输出，以减少AI自由发挥的空间
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
                safety_settings=safety_settings
            )
            
            # Gemini在JSON模式下会直接返回纯净的JSON文本
            entity_data = json.loads(response.text)
            
            # --- 步骤C: 将新结果存入缓存 ---
            if redis:
                print(f"  - Storing new data in cache. Key: {cache_key}")
                redis.set(cache_key, json.dumps(entity_data), ex=86400) # 24小时过期

            # 返回新生成的数据
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(entity_data).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
