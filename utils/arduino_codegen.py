from typing import Dict

def to_arduino_sketch(netlist: Dict) -> str:
    """
    Very simple Arduino sketch generator:
    - If Arduino Uno + LED via D13, blink.
    - If button on D2, read and mirror to LED D13.
    - For ESP32-CAM, emit a stub with comment to use CameraWebServer example.
    Otherwise, produce a comment-only skeleton.
    """
    comps = netlist.get("components", [])
    conns = netlist.get("connections", [])

    model = ""
    for c in comps:
        if c.get("type") == "microcontroller":
            model = (c.get("model") or "").lower()
            break

    if "esp32-cam" in model:
        return (
            "// ESP32-CAM sketch\n"
            "// Flash the standard CameraWebServer example from Arduino IDE (ESP32 board package).\n"
            "// Select AI Thinker ESP32-CAM, set correct pins in the example, and upload.\n\n"
            "void setup() {\n"
            "  // Use CameraWebServer example. This is a placeholder.\n"
            "}\n\n"
            "void loop() {\n"
            "}\n"
        )

    if "arduino uno" in model:
        use_led_d13 = any(a=="U1:D13" or b=="U1:D13" for a,b in conns)
        button_d2  = any(a=="U1:D2"  or b=="U1:D2"  for a,b in conns)

        if use_led_d13 and not button_d2:
            return (
                "// Arduino Uno: Blink LED on D13\n"
                "void setup(){ pinMode(13, OUTPUT); }\n"
                "void loop(){ digitalWrite(13, HIGH); delay(500); digitalWrite(13, LOW); delay(500); }\n"
            )
        if use_led_d13 and button_d2:
            return (
                "// Arduino Uno: Button on D2 controls LED on D13\n"
                "void setup(){ pinMode(2, INPUT_PULLUP); pinMode(13, OUTPUT); }\n"
                "void loop(){ int p=digitalRead(2); digitalWrite(13, p==LOW ? HIGH : LOW); }\n"
            )
        return (
            "// Arduino Uno skeleton generated from netlist\n"
            "void setup(){ /* TODO: set pinModes based on connections */ }\n"
            "void loop(){ /* TODO */ }\n"
        )

    return (
        "// Generic sketch skeleton\n"
        "void setup(){ }\n"
        "void loop(){ }\n"
    )
