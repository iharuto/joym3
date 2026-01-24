import hid, time, sys, json, os

from Quartz.CoreGraphics import (
    CGEventCreate, CGEventGetLocation,
    CGEventCreateMouseEvent, CGEventPost,
    kCGHIDEventTap, kCGEventMouseMoved,
    kCGEventLeftMouseDown, kCGEventLeftMouseUp,
    kCGEventRightMouseDown, kCGEventRightMouseUp,
    CGEventCreateKeyboardEvent,
    kCGEventKeyDown, kCGEventKeyUp,
)

CONFIG_PATH = "/Users/haruto/joym3/config/runtime_config.json"

# macOS key codes mapping
KEY_CODES = {
    "space": 49, "escape": 53, "return": 36,
    "tab": 48, "delete": 51, "a": 0, "b": 11,
    "c": 8, "d": 2, "e": 14, "f": 3,
    "g": 5, "h": 4, "i": 34, "j": 38,
    "k": 40, "l": 37, "m": 46, "n": 45,
    "o": 31, "p": 35, "q": 12, "r": 15,
    "s": 1, "t": 17, "u": 32, "v": 9,
    "w": 13, "x": 7, "y": 16, "z": 6,
}

def load_config():
    """Load configuration from JSON file."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config from {CONFIG_PATH}: {e}")
            return None
    return None

def current_mouse_pos():
    ev = CGEventCreate(None)
    loc = CGEventGetLocation(ev)
    return float(loc.x), float(loc.y)

def post_move_abs(x, y):
    ev = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), 0)
    CGEventPost(kCGHIDEventTap, ev)

def click(button="left"):
    x, y = current_mouse_pos()
    if button == "left":
        down, up, btn = kCGEventLeftMouseDown, kCGEventLeftMouseUp, 0
    else:
        down, up, btn = kCGEventRightMouseDown, kCGEventRightMouseUp, 1
    CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(None, down, (x, y), btn))
    CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(None, up,   (x, y), btn))

def press_key(key_name):
    """Simulate a keyboard key press."""
    key_name = key_name.lower()
    if key_name in KEY_CODES:
        keycode = KEY_CODES[key_name]
        ev_down = CGEventCreateKeyboardEvent(None, keycode, True)
        ev_up = CGEventCreateKeyboardEvent(None, keycode, False)
        CGEventPost(kCGHIDEventTap, ev_down)
        CGEventPost(kCGHIDEventTap, ev_up)
    else:
        print(f"Warning: Unknown key '{key_name}'")

def find_joycon_r():
    hits = [d for d in hid.enumerate() if (d.get("product_string") or "") == "Joy-Con (R)"]
    if len(hits) == 0:
        print("Joy-Con (R) が見つかりませんでした"); return None
    if len(hits) > 1:
        print("Joy-Con (R) が複数見つかりました（想定外）")
        for h in hits:
            print(f"VID={h['vendor_id']:04x} PID={h['product_id']:04x} path={h.get('path')}")
        return None
    return hits[0]

HAT_TO_VEC = {
    0x08: (0, 0),
    0x02: (0, -1),
    0x03: (1, -1),
    0x04: (1, 0),
    0x05: (1, 1),
    0x06: (0, 1),
    0x07: (-1, 1),
    0x00: (-1, 0),
    0x01: (-1, -1),
}

A_MASK = 0x01
B_MASK = 0x04
X_MASK = 0x02
Y_MASK = 0x08

# Load configuration
config = load_config()
if config and "speed" in config:
    TICK = 1 / config["speed"]["tick_hz"]
    STEP_MIN = config["speed"]["step_min"]
    STEP_MAX = config["speed"]["step_max"]
    RAMP_SEC = config["speed"]["ramp_sec"]
else:
    # Default values
    TICK = 1/120
    STEP_MIN = 5
    STEP_MAX = 20
    RAMP_SEC = 0.7

info = find_joycon_r()
if info is None:
    sys.exit(1)

dev = hid.Device(path=info["path"])
dev.nonblocking = True   # ★ここがあなたの環境では正解

print(f"Opened {info.get('product_string')}  VID={info['vendor_id']:04x} PID={info['product_id']:04x}")
print("Hold D-pad/Stick to move continuously | A: left click | B: right click | Ctrl+C to stop")

def handle_button(button_name, is_pressed, was_pressed):
    """Handle button press based on config."""
    if is_pressed and not was_pressed:  # Button just pressed
        if config and "buttons" in config:
            btn_config = config["buttons"].get(button_name, {})
            action = btn_config.get("action")
            value = btn_config.get("value")

            if action == "mouse_click" and value:
                click(value)
            elif action == "keyboard" and value:
                press_key(value)
        else:
            # Default behavior
            if button_name == "A":
                click("left")
            elif button_name == "B":
                click("right")

vx = vy = 0
moving_since = None
last_a = last_b = last_x = last_y = False

next_tick = time.perf_counter()

try:
    while True:
        data = dev.read(64)
        if data:
            b = bytes(data)
            if len(b) >= 4:
                btn1 = b[1]
                hat  = b[3]

                vx, vy = HAT_TO_VEC.get(hat, (0, 0))
                if vx or vy:
                    if moving_since is None:
                        moving_since = time.perf_counter()
                else:
                    moving_since = None

                a_now = (btn1 & A_MASK) != 0
                b_now = (btn1 & B_MASK) != 0
                x_now = (btn1 & X_MASK) != 0
                y_now = (btn1 & Y_MASK) != 0

                handle_button("A", a_now, last_a)
                handle_button("B", b_now, last_b)
                handle_button("X", x_now, last_x)
                handle_button("Y", y_now, last_y)

                last_a, last_b, last_x, last_y = a_now, b_now, x_now, y_now

        now = time.perf_counter()
        if now >= next_tick:
            next_tick += TICK

            if vx or vy:
                t = 0.0 if moving_since is None else (now - moving_since)
                alpha = min(max(t / RAMP_SEC, 0.0), 1.0)
                step = STEP_MIN + (STEP_MAX - STEP_MIN) * alpha

                x, y = current_mouse_pos()
                post_move_abs(x + vx * step, y + vy * step)

        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    dev.close()
    print("\nclosed")