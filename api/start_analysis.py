# api/start_analysis.py
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import uuid

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            robot_name = parse_qs(urlparse(self.path).query).get('robot', [None])[0]
            if not robot_name:
                raise ValueError("'robot' parameter is missing.")

            task_id = str(uuid.uuid4())
            
            # 定义实体识别逻辑
            entities = [{"name": robot_name}]
            robot_name_lower = robot_name.lower()
            if "figure" in robot_name_lower:
                entities.extend([{"name": "Optimus"}, {"name": "Atlas"}])
            elif "optimus" in robot_name_lower:
                entities.extend([{"name": "Figure 02"}, {"name": "Atlas"}])
            elif "atlas" in robot_name_lower:
                entities.extend([{"name": "Figure 02"}, {"name": "Optimus"}])
            else: # 默认竞品
                entities.extend([{"name": "Optimus"}, {"name": "Figure 02"}])
            
            response_data = {"task_id": task_id, "entities": entities}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
