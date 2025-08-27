from pathlib import Path
from typing import Dict, Tuple, Optional
import matplotlib
matplotlib.use("Agg")  # ✅ Disable GUI popups from matplotlib

import schemdraw
import schemdraw.elements as elm


def _draw_rect(d: schemdraw.Drawing, center: Tuple[float, float], w: float, h: float, title: Optional[str] = None):
    cx, cy = center
    x0, y0 = cx - w / 2, cy - h / 2
    x1, y1 = cx + w / 2, cy + h / 2
    d.add(elm.Line().at((x0, y0)).to((x1, y0)))
    d.add(elm.Line().at((x1, y0)).to((x1, y1)))
    d.add(elm.Line().at((x1, y1)).to((x0, y1)))
    d.add(elm.Line().at((x0, y1)).to((x0, y0)))
    if title:
        d.add(elm.Label().at((cx, y1 + 0.6)).label(title))
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def _pin_label(d: schemdraw.Drawing, xy, text, dx, dy):
    d.add(elm.Dot(open=True).at(xy))
    d.add(elm.Label().at((xy[0] + dx, xy[1] + dy)).label(text))


def draw_from_netlist(netlist: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    placements: Dict[str, dict] = {}

    # ✅ show=False prevents schemdraw from opening preview window
    with schemdraw.Drawing(file=str(out_path), show=False) as d:
        d.config(unit=3)
        something = False

        # --- MCU block with only used pins ---
        mcu = next((c for c in netlist.get("components", []) if c.get("type") == "microcontroller"), None)
        used_pins = set()
        for a, b in netlist.get("connections", []):
            if ":" in a:
                used_pins.add(a.split(":", 1)[1])
            if ":" in b:
                used_pins.add(b.split(":", 1)[1])

        if mcu:
            model = (mcu.get("model") or "")
            box = _draw_rect(d, (0.0, 0.0), 10.0, 8.0, title=model)
            placements[mcu["id"]] = {"type": "mcu", "box": box, "pins": {}}
            something = True

            left_candidates = ["GND", "3.3V", "5V", "RESET"]
            right_candidates = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13"]

            if "esp32" in model.lower():
                left_candidates = ["GND", "5V"]
                right_candidates = [
                    "CAM_PWDN", "CAM_SIOD", "CAM_SIOC", "CAM_XCLK",
                    "CAM_D0", "CAM_D1", "CAM_D2", "CAM_D3",
                    "CAM_D4", "CAM_D5", "CAM_D6", "CAM_D7"
                ]

            left_pins = [p for p in left_candidates if p in used_pins]
            right_pins = [p for p in right_candidates if p in used_pins]

            total_left = max(1, len(left_pins))
            for i, pname in enumerate(left_pins):
                y = box["y1"] - (i + 1) * ((box["y1"] - box["y0"]) / (total_left + 1))
                x = box["x0"]
                d.add(elm.Line().at((x, y)).to((x - 1.2, y)))
                _pin_label(d, (x, y), pname, -1.4, 0)
                placements[mcu["id"]]["pins"][pname] = (x - 1.2, y)

            total_right = max(1, len(right_pins))
            for i, pname in enumerate(right_pins):
                y = box["y1"] - (i + 1) * ((box["y1"] - box["y0"]) / (total_right + 1))
                x = box["x1"]
                d.add(elm.Line().at((x, y)).to((x + 1.2, y)))
                _pin_label(d, (x, y), pname, 1.4, 0)
                placements[mcu["id"]]["pins"][pname] = (x + 1.2, y)

        # --- Place other components ---
        grid_x, grid_y, step_y = 14.0, 8.0, 3.0
        next_row = 0

        def place(comp):
            nonlocal next_row, something
            ctype = (comp.get("type") or "").lower()
            cid = comp.get("id") or f"C{next_row+1}"
            pos = (grid_x, grid_y - next_row * step_y)
            next_row += 1

            if ctype == "resistor":
                d.add(elm.Resistor().at(pos).right().label(comp.get("value", "")))
                placements[cid] = {"type": "resistor", "anchor": pos}; something = True
            elif ctype == "led":
                d.add(elm.LED().at(pos).right().label("LED"))
                placements[cid] = {"type": "led", "anchor": pos}; something = True
            elif ctype == "button":
                d.add(elm.Switch().at(pos).right().label("Button"))
                placements[cid] = {"type": "button", "anchor": pos}; something = True
            elif ctype in ("battery", "voltage_source"):
                d.add(elm.SourceV().at(pos).down().label(comp.get("value", "V")))
                placements[cid] = {"type": "voltage_source", "anchor": pos}; something = True
            elif ctype == "camera_module":
                bx, by = pos; w, h = 3.0, 2.0
                d.add(elm.Line().at((bx - w/2, by - h/2)).to((bx + w/2, by - h/2)))
                d.add(elm.Line().at((bx + w/2, by - h/2)).to((bx + w/2, by + h/2)))
                d.add(elm.Line().at((bx + w/2, by + h/2)).to((bx - w/2, by + h/2)))
                d.add(elm.Line().at((bx - w/2, by + h/2)).to((bx - w/2, by - h/2)))
                d.add(elm.Label().at((bx, by + h/2 + 0.3)).label(comp.get("model", "CAM")))
                placements[cid] = {"type": "camera", "anchor": pos}; something = True
            elif ctype == "gnd":
                d.add(elm.Ground().at(pos))
                placements[cid] = {"type": "gnd", "anchor": pos}; something = True
            else:
                bx, by = pos; w, h = 3.0, 2.0
                d.add(elm.Line().at((bx - w/2, by - h/2)).to((bx + w/2, by - h/2)))
                d.add(elm.Line().at((bx + w/2, by - h/2)).to((bx + w/2, by + h/2)))
                d.add(elm.Line().at((bx + w/2, by + h/2)).to((bx - w/2, by + h/2)))
                d.add(elm.Line().at((bx - w/2, by + h/2)).to((bx - w/2, by - h/2)))
                d.add(elm.Label().at((bx, by + h/2 + 0.4)).label(ctype or "blk"))
                placements[cid] = {"type": "block", "anchor": pos}; something = True

        for c in netlist.get("components", []):
            if (c.get("type") or "").lower() == "microcontroller":
                continue
            place(c)

        def pin_xy(ref):
            if ":" not in ref:
                return None
            cid, pin = ref.split(":", 1)
            pd = placements.get(cid)
            if not pd:
                return None
            t = pd.get("type")
            if t == "mcu":
                return pd["pins"].get(pin)
            ax, ay = pd.get("anchor", (0.0, 0.0))
            if t in ("resistor", "led", "button"):
                return (ax, ay) if pin in ("1", "+", "in", "a") else (ax + 2.0, ay)
            if t == "voltage_source":
                return (ax, ay) if pin in ("+", "pos", "1") else (ax, ay - 2.0)
            if t == "camera":
                return (ax - 0.6, ay)
            if t == "gnd":
                return (ax, ay)
            return (ax, ay)

        for a, b in netlist.get("connections", []):
            p1, p2 = pin_xy(a), pin_xy(b)
            if p1 and p2:
                d.add(elm.Line().at(p1).tox(p2[0]))
                d.add(elm.Line().at((p2[0], p1[1])).toy(p2[1]))
                d.add(elm.Dot().at(p2))
                something = True

        if not something:
            d.add(elm.Resistor().label("R"))

    return out_path
