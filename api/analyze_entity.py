# api/analyze_entity.py (Upstash Cache Version)

# ... (其他imports保持不变)
from upstash_redis import Redis # 引入新的库

# --- 配置与初始化 ---
# ... (API Key部分保持不变)
# 从Vercel自动注入的环境变量中初始化Redis客户端
redis = Redis.from_env()

# ... (professional_search, extract_json_from_text 函数保持不变)

# --- 主处理逻辑 ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # ... (robot_name 解析保持不变)
            
            # 创建一个标准化的缓存键
            cache_key = f"robot_entity:{robot_name.strip().lower().replace(' ', '_')}"

            # --- 步骤A: 检查缓存 ---
            print(f"  - Checking Upstash cache with key: {cache_key}")
            cached_data = redis.get(cache_key)
            if cached_data:
                print("  - ✅ Cache HIT! Returning cached data.")
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # Redis返回的是字符串，需要先解析成JSON对象
                self.wfile.write(json.dumps(json.loads(cached_data)).encode('utf-8'))
                return

            print("  - ❌ Cache MISS. Proceeding to live analysis.")
            
            # --- 步骤B: 实时分析 (逻辑不变) ---
            # ...
            entity_data = ... # (获取到entity_data)

            # --- 步骤C: 将新结果存入缓存 ---
            print(f"  - Storing new data in Upstash cache. Key: {cache_key}")
            # Redis需要我们将Python字典转换成JSON字符串再存入
            # ex=86400 设置过期时间为24小时
            redis.set(cache_key, json.dumps(entity_data), ex=86400)

            # 返回新生成的数据
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(entity_data).encode('utf-8'))
            
        except Exception as e:
            # ... (错误处理保持不变)
            pass
