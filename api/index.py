# api/index.py (V4.4 - Defensive Chaining)
# ... (所有imports和辅助函数保持不变) ...

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ... (GET请求处理的开头部分保持不变) ...
        try:
            # ... (Stage 1: Information Gathering 保持不变) ...
            
            print(f"--- Stage 2: Executing Robust Analysis Task Chain ---")
            
            t1_prompt = f"Based on the provided text about '{robot_name}', analyze its technical architecture (Perception, Control, Locomotion). List key functional components for each system. Output ONLY as a valid JSON object like this: {{{{ \"perception_components\": [...], \"control_components\": [...], \"locomotion_components\": [...] }}}}.\n\nText: {comprehensive_text}"
            t1_output = call_gemini(t1_prompt, "T1_Tech_Architecture")
            
            perception_comps = t1_output.get("perception_components", []) if isinstance(t1_output, dict) else []
            control_comps = t1_output.get("control_components", []) if isinstance(t1_output, dict) else []
            locomotion_comps = t1_output.get("locomotion_components", []) if isinstance(t1_output, dict) else []

            t2_prompt = f"""Given the text and these functional components: {{ "perception": {json.dumps(perception_comps)}, "control": {json.dumps(control_comps)}, "locomotion": {json.dumps(locomotion_comps)} }}. Map functions to specific hardware modules. Output ONLY as a valid JSON object like this: {{{{ "hardware_mappings": [{{ "function": "...", "hardware": "...", "purpose": "..." }}] }}}}.\n\nText: {comprehensive_text}"""
            t2_output = call_gemini(t2_prompt, "T2_Hardware_Mapping")

            hardware_for_t3 = t2_output.get("hardware_mappings", []) if isinstance(t2_output, dict) else []

            t3_prompt = f"""For each hardware module: {json.dumps(hardware_for_t3)}. Find potential suppliers from the text. Output ONLY as a valid JSON object like this: {{{{ "supplier_mappings": [{{ "hardware": "...", "suppliers": [{{ "name": "...", "country": "..." }}] }}] }}}}.\n\nText: {comprehensive_text}"""
            t3_output = call_gemini(t3_prompt, "T3_Supplier_Matching")
            
            t4_prompt = f"Based on all the text, analyze the market landscape for '{robot_name}'. Output ONLY as a valid JSON object with a single key 'market_analysis_summary'.\n\nText: {comprehensive_text}"
            t4_output = call_gemini(t4_prompt, "T4_Market_Analysis")

            t5_prompt = f"""Synthesize T1, T2, and T3 data to create nodes and links for a Sankey diagram (Function -> Hardware -> Supplier). Output ONLY as a valid JSON object like this: {{{{ "nodes": [...], "links": [...] }}}}.\n\nData: T1={json.dumps(t1_output)}, T2={json.dumps(t2_output)}, T3={json.dumps(t3_output)}"""
            t5_output = call_gemini(t5_prompt, "T5_Sankey_Data")

            # ... (Stage 3: Aggregating Final Report 保持不变) ...
            
        except Exception as e:
            # ... (错误处理保持不变) ...
