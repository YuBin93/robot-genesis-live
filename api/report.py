# api/report.py (V3.1 - Final Fusion Version)

from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from duckduckgo_search import DDGS
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 1. 配置与初始化 (保持不变) ---
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. 辅助函数 (scrape_url, extract_json_from_text) (保持不变) ---
# ...

# --- 3. 终极的、融合的Prompt构建函数 ---
def build_final_fused_report_prompt(compiled_data_text):
    """
    这个Prompt强制AI同时进行微观技术拆解和宏观战略分析。
    """
    return f"""
    You are a world-class senior analyst, with dual expertise in robotics engineering and market strategy.
    Your mission is to generate a deeply researched, multi-layered strategic report based on the compiled data for several robots.
    The report must be a single, valid JSON object.

    The process is twofold:
    1.  **Bottom-up Technical Teardown**: For each robot, perform a detailed technical teardown, identifying its architecture, key components, and potential suppliers.
    2.  **Top-down Strategic Synthesis**: Based on the teardown data, perform a competitive analysis and identify market trends.

    The final JSON output MUST strictly follow this nested structure:

    {{
      "executive_summary": "A high-level summary of the competitive landscape and key findings.",
      "competitive_landscape": [
        {{
          "robot_name": "Name of the first robot",
          "manufacturer": "Its manufacturer",
          "technical_teardown": {{
            "perception_system": {{ "key_components": ["List detailed components"], "potential_suppliers": ["List potential suppliers"] }},
            "locomotion_system": {{ "key_components": ["..."], "potential_suppliers": ["..."] }},
            "control_ai_system": {{ "key_components": ["..."], "potential_suppliers": ["..."] }}
          }},
          "strategic_analysis": {{
            "strengths": ["List strengths derived from the teardown, e.g., 'Advanced perception suite from NVIDIA.'"],
            "weaknesses": ["List weaknesses, e.g., 'Reliance on a single supplier for core AI.'"],
            "market_position": "Describe its market positioning."
          }}
        }},
        // ... (similar objects for other robots) ...
      ],
      "market_trends_and_predictions": {{
        "key_technology_trends": ["Identify common tech trends observed from all teardowns, e.g., 'Trend towards using automotive-grade LiDAR.'"],
        "supply_chain_map": ["Identify common key suppliers across all robots (e.g., NVIDIA, OpenAI) and what this implies."],
        "future_outlook": "Provide a forward-looking prediction for the market."
      }},
      "data_confidence": {{
        "assessment": "Briefly assess the quality and completeness of the source data.",
        "identified_gaps": ["List key information that is still missing across all robots."]
      }}
    }}

    ### Compiled Data from Multiple Sources:
    {compiled_data_text}

    ### Complete Strategic Report (JSON):
    """

# --- 4. Serverless Function 主处理逻辑 (与V3.0基本相同，只更换Prompt) ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ... (此部分与上一版完全相同，只在最后调用新的Prompt) ...
        try:
            # ... (Stage 1 & 2: Entity ID and Info Gathering) ...
            
            # --- Stage 3: Generating Final FUSED Report ---
            print("--- Stage 3: Generating Final Fused Strategic Report ---")
            compiled_data_text = "\n\n".join([f"--- Data for {name} ---\n{text}" for name, text in compiled_data.items()])
            
            # --- 核心改变：调用我们全新的融合Prompt ---
            final_prompt = build_final_fused_report_prompt(compiled_data_text)
            
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            final_response = model.generate_content(final_prompt, safety_settings=safety_settings)
            
            report_data = extract_json_from_text(final_response.text)
            report_data["_source_urls"] = source_urls

            # ... (成功返回) ...
        except Exception as e:
            # ... (错误处理) ...
            pass
    # ... (gather_info_for_entity 保持不变)
