# api/analyze_entity.py (Final Robust Initialization - Full Code)

from http.server import BaseHTTPRequestHandler
import json, os, re, requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import google.generativeai as genai
from upstash_redis import Redis

# --- 1. CONFIG & INIT ---
API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

redis = None
redis_init_error = None
try:
    redis_url = os.getenv("UPSTASH_REDIS_REST_URL")
    redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not redis_url or not redis_token:
        raise ValueError("Upstash Redis credentials (URL or Token) are not set in environment variables.")
    redis = Redis(url=redis_url, token=redis_token)
    redis.ping()
    print("✅ Successfully connected to Upstash Redis.")
except Exception as e:
    redis_init_error = e
    print(f"❌ Failed to initialize Redis client: {e}")

# --- 2. HELPER FUNCTIONS ---
def professional_search(query):
    if not SERPER_API_KEY: raise ValueError("SERPER_API_KEY not set.")
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": 5})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=payload, timeout=15)
    response.raise_for_status()
    return response.json()

def extract_json_from_text(text):
    match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
    if match: return json.loads(match.group(1))
    start_index = text.find('{'); end_index = text.rfind('}')
    if start_index != -1 and end_index != -1: return json.loads(text[start_index : end_index + 1])
    raise json.JSONDecodeError("Could not find valid JSON.", text, 0)

# --- 3. MAIN HANDLER ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if redis is None:
            self.send_response(500); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"error": "Server configuration error: Failed to connect to cache database.", "details": str(redis_init_error)}).encode('utf-8'))
            return
        
        try:
            if not API_KEY: raise ValueError("GEMINI_API_KEY not set.")
            robot_name_raw = parse_qs(urlparse(self.path).query).get('name', [None])[0]
            if not robot_name_raw: raise ValueError("'name' parameter is missing.")
            
            robot_name = robot_name_raw.strip().lower()
            cache_key = f"robot_entity:{robot_name.replace(' ', '_')}"

            print(f"--- Analyzing entity: {robot_name} ---")
            print(f"  - Checking cache with key: {cache_key}")
            cached_data = redis.get(cache_key)
            if cached_data:
                print("  - ✅ Cache HIT! Returning cached data.")
                self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(json.loads(cached_data)).encode('utf-8'))
                return

            print("  - ❌ Cache MISS. Proceeding to live analysis.")
            
            search_results = professional_search(f"{robot_name} robot specifications")
            context = "\n".join([f"Title: {r.get('title', '')}\nSnippet: {r.get('snippet', '')}" for r in search_results.get('organic', [])])
            if not context.strip(): raise ValueError("Search returned no content.")

            prompt = f"""Based on the provided search results for '{robot_name}', extract key information. Output ONLY as a valid JSON object like this: {{{{ "name": "Full official name", "manufacturer": "The manufacturer", "summary": "A one-sentence summary.", "specs": {{{{ "Weight": "...", "Payload": "..." }}}} }}}}
            
            ### Search Results:
            {context}
            ### JSON Output:
            """
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            response = model.generate_content(prompt, safety_settings=safety_settings)
            
            entity_data = extract_json_from_text(response.text)
            
            print(f"  - Storing new data in cache. Key: {cache_key}")
            redis.set(cache_key, json.dumps(entity_data), ex=86400)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(entity_data).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
