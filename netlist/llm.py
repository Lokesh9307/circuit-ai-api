import os, json
from typing import Optional, Dict, Any
from utils.json_extract import extract_json_block

try:
    import google.generativeai as genai
    _GEMINI_IMPORTED = True
except Exception:
    genai = None
    _GEMINI_IMPORTED = False


NETLIST_JSON_EXAMPLE = {
    "components": [
        {"id": "U1", "type": "microcontroller", "model": "ESP32-CAM"},
        {"id": "CAM1", "type": "camera_module", "model": "OV2640"},
        {"id": "V1", "type": "voltage_source", "value": "5V"},
        {"id": "GND", "type": "gnd"},
    ],
    "connections": [
        ["V1:+", "U1:5V"], ["V1:-", "U1:GND"],
        ["U1:CAM_PWDN","CAM1:PWDN"], ["U1:CAM_SIOD","CAM1:SIOD"], ["U1:CAM_SIOC","CAM1:SIOC"],
        ["U1:CAM_XCLK","CAM1:XCLK"], ["U1:CAM_D0","CAM1:D0"], ["U1:CAM_D1","CAM1:D1"],
        ["CAM1:GND","U1:GND"]
    ],
    "explanation": "Example only."
}


def call_gemini_for_netlist(prompt_text: str) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not (_GEMINI_IMPORTED and api_key):
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        sys_prompt = (
            "You are a netlist generator. Return ONLY JSON with keys 'components' and 'connections', "
            "and a short 'explanation'. Each component: {id, type, value?, model?}. For microcontrollers include "
            "model exactly (e.g., 'ESP32-CAM' or 'Arduino Uno'). Connections are pairs like "
            "['U1:5V','V1:+'] or ['U1:D13','R1:1']. The 'explanation' should be step-by-step (2-10 lines). "
            "No extra prose outside JSON."
        )
        user_text = f"User request: {prompt_text}\n\nSchema example: {json.dumps(NETLIST_JSON_EXAMPLE)}"
        resp = model.generate_content([sys_prompt, user_text])
        raw = (resp.text or "").strip()
        jtxt = extract_json_block(raw)
        if not jtxt:
            return None
        data = json.loads(jtxt)
        if isinstance(data, dict) and "components" in data:
            return data
    except Exception:
        return None
    return None


def call_gemini_for_explanation(netlist: Dict, query:str) -> str:
    """
    Ask Gemini to generate a human-readable explanation from the given netlist.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not (_GEMINI_IMPORTED and api_key):
        return "Explanation unavailable (Gemini API not configured)."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        sys_prompt = (
            f"You are an electronics instructor. Explain the given circuit netlist and {query} step-by-step. "
            "Write in clear, numbered steps (max 10). Avoid JSON, only natural language."
        )
        user_text = f"Netlist: {json.dumps(netlist)}"
        resp = model.generate_content([sys_prompt, user_text])
        return (resp.text or "Explanation unavailable.").strip()
    except Exception as e:
        return f"Explanation generation failed: {e}"


def call_gemini_for_arduino(netlist: Dict,query:str) -> str:
    """
    Ask Gemini to generate an Arduino IDE compatible sketch from the netlist.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not (_GEMINI_IMPORTED and api_key):
        return "// Arduino code unavailable (Gemini API not configured)."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        sys_prompt = (
            f"You are an Arduino code generator. Write a complete sketch (C++ for Arduino IDE) based on the netlist and {query}. "
            "Handle Arduino Uno, ESP32-CAM, sensors, actuators, LEDs, buttons, etc. "
            "Return ONLY valid Arduino C++ code, no markdown formatting."
        )
        user_text = f"Netlist: {json.dumps(netlist)}"
        resp = model.generate_content([sys_prompt, user_text])
        return (resp.text or "// Code unavailable.").strip()
    except Exception as e:
        return f"// Arduino code generation failed: {e}"
