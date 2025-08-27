def build_explanation(netlist: dict) -> str:
    """
    Build an explanation of the circuit.
    Priority:
      1. If the netlist already has an 'explanation' (LLM-provided), use it.
      2. If ESP32-related, return specific ESP32 connection guidance.
      3. Otherwise, return a generic fallback explanation.
    """
    # Case 1: Use explanation from LLM if available
    if isinstance(netlist, dict) and netlist.get("explanation"):
        return netlist["explanation"]

    # Case 2: Special rule for ESP32
    is_esp32 = any(
        "esp32" in (c.get("model", "").lower()) 
        for c in netlist.get("components", [])
    )
    if is_esp32:
        return (
            "Step-by-step guide for ESP32-based circuit:\n"
            "1) Connect a stable 5V supply to the 5V and GND pins of the ESP32 board.\n"
            "2) If using a camera module (e.g., OV2640), connect SIOD, SIOC, XCLK, and D0–D7 lines to the ESP32 camera pins.\n"
            "3) Ensure all devices share a common ground.\n"
            "4) Upload firmware (e.g., Arduino IDE ESP32 Camera WebServer example).\n"
            "5) After flashing, open the ESP32’s IP address in a browser to access the camera stream.\n"
            "6) Use a reliable 5V source, as unstable USB power may cause random resets."
        )

    # Case 3: Generic fallback
    return (
        "This circuit connects power, ground, and components as shown in the diagram. "
        "Follow the wiring in the schematic to ensure correct connections between the modules."
    )
