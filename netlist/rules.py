import re
from typing import Dict, Any

def rule_based_netlist(query: str) -> Dict[str, Any]:
    t = (query or "").lower()
    components = []
    connections = []

    # ESP32-CAM detection
    is_esp32cam = bool(re.search(r"\besp32[\s-]?cam\b|\besp32\b", t))
    if is_esp32cam:
        components += [
            {"id": "U1", "type": "microcontroller", "model": "ESP32-CAM"},
            {"id": "CAM1", "type": "camera_module", "model": "OV2640"},
            {"id": "V1", "type": "voltage_source", "value": "5V"},
            {"id": "GND", "type": "gnd"},
        ]
        connections += [["V1:+","U1:5V"],["V1:-","U1:GND"],["V1:+","CAM1:5V"],["CAM1:GND","U1:GND"]]
        for p in ["PWDN","SIOD","SIOC","XCLK","D0","D1","D2","D3","D4","D5","D6","D7"]:
            connections.append([f"U1:CAM_{p}", f"CAM1:{p}"])
        explanation = (
            "Use ESP32-CAM (U1) powered by a stable 5V supply. "
            "Connect OV2640 (CAM1) camera pins (SIOD/SIOC/XCLK/D0..D7) to ESP32 camera pins. "
            "Tie grounds together. Flash camera streaming firmware and view the stream in a browser."
        )
        return {"components": components, "connections": connections, "explanation": explanation}

    # Generic Arduino/LED/Button detection
    volt = 5
    m = re.search(r"(\d+(?:\.\d+)?)\s*v", t)
    if m:
        try: volt = float(m.group(1))
        except Exception: volt = 5
    components.append({"id":"V1","type":"voltage_source","value":f"{volt:g}V"})

    if "arduino" in t:
        components.append({"id":"U1","type":"microcontroller","model":"Arduino Uno"})
        connections += [["V1:+","U1:5V"],["V1:-","U1:GND"]]

    if "led" in t:
        components.append({"id":"D1","type":"led"})
        # use 220Ω default
        components.append({"id":"R1","type":"resistor","value":"220Ω"})
        if "d13" in t:
            connections += [["U1:D13","R1:1"],["R1:2","D1:+"],["D1:-","U1:GND"]]
        else:
            connections += [["V1:+","R1:1"],["R1:2","D1:+"],["D1:-","V1:-"]]

    if re.search(r"\b(button|switch)\b", t):
        components.append({"id":"S1","type":"button"})
        if "d2" in t:
            connections += [["S1:1","U1:D2"],["S1:2","U1:GND"]]
        else:
            connections += [["S1:1","V1:+"],["S1:2","V1:-"]]

    explanation = "Fallback: wire power/ground and components as shown in the diagram. Follow the connections list."
    return {"components": components, "connections": connections, "explanation": explanation}
