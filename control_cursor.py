import hid, time, sys, json, os
import shared_state

from Quartz.CoreGraphics import (
    CGEventCreate, CGEventGetLocation,
    CGEventCreateMouseEvent, CGEventPost,
    kCGHIDEventTap, kCGEventMouseMoved,
    kCGEventLeftMouseDown, kCGEventLeftMouseUp,
    kCGEventRightMouseDown, kCGEventRightMouseUp,
    kCGEventLeftMouseDragged,
    CGEventCreateKeyboardEvent,
    kCGEventKeyDown, kCGEventKeyUp,
    CGDisplayBounds, CGMainDisplayID,
    CGEventCreateScrollWheelEvent,
    CGEventSetFlags,
    kCGEventFlagMaskCommand,
    kCGEventFlagMaskShift,
    CGEventSetIntegerValueField,
    kCGMouseEventClickState,
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
    "left": 123,   # Left arrow
    "right": 124,  # Right arrow
    "=": 24,       # Equals (for zoom)
    "-": 27,       # Minus (for zoom)
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

def get_screen_dimensions():
    """Get the main screen dimensions."""
    main_display = CGMainDisplayID()
    bounds = CGDisplayBounds(main_display)
    width = int(bounds.size.width)
    height = int(bounds.size.height)
    return width, height

def clamp_coordinates(x, y, screen_width, screen_height):
    """
    Clamp coordinates to screen boundaries.

    Args:
        x: X coordinate
        y: Y coordinate
        screen_width: Maximum screen width
        screen_height: Maximum screen height

    Returns:
        Tuple of (clamped_x, clamped_y)
    """
    clamped_x = min(max(0, x), screen_width - 1)
    clamped_y = min(max(0, y), screen_height - 1)
    return clamped_x, clamped_y

def current_mouse_pos():
    ev = CGEventCreate(None)
    loc = CGEventGetLocation(ev)
    return float(loc.x), float(loc.y)

def post_move_abs(x, y):
    ev = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), 0)
    CGEventSetFlags(ev, 0)  # Clear modifier flags
    CGEventPost(kCGHIDEventTap, ev)

def click(button="left"):
    x, y = current_mouse_pos()
    if button == "left":
        down, up, btn = kCGEventLeftMouseDown, kCGEventLeftMouseUp, 0
    else:
        down, up, btn = kCGEventRightMouseDown, kCGEventRightMouseUp, 1

    # Create events and explicitly clear modifier flags
    ev_down = CGEventCreateMouseEvent(None, down, (x, y), btn)
    ev_up = CGEventCreateMouseEvent(None, up, (x, y), btn)
    CGEventSetFlags(ev_down, 0)  # No modifier flags
    CGEventSetFlags(ev_up, 0)    # No modifier flags

    CGEventPost(kCGHIDEventTap, ev_down)
    CGEventPost(kCGHIDEventTap, ev_up)

def double_click(button="left"):
    """Execute a double-click by posting two click events with proper timing."""
    x, y = current_mouse_pos()
    if button == "left":
        down_type = kCGEventLeftMouseDown
        up_type = kCGEventLeftMouseUp
        btn_num = 0
    else:
        down_type = kCGEventRightMouseDown
        up_type = kCGEventRightMouseUp
        btn_num = 1

    # First click (click count = 1)
    down1 = CGEventCreateMouseEvent(None, down_type, (x, y), btn_num)
    up1 = CGEventCreateMouseEvent(None, up_type, (x, y), btn_num)
    CGEventSetIntegerValueField(down1, kCGMouseEventClickState, 1)
    CGEventSetIntegerValueField(up1, kCGMouseEventClickState, 1)
    CGEventSetFlags(down1, 0)  # No modifier flags
    CGEventSetFlags(up1, 0)    # No modifier flags

    CGEventPost(kCGHIDEventTap, down1)
    CGEventPost(kCGHIDEventTap, up1)

    # Small delay between clicks (15ms is typical)
    time.sleep(0.015)

    # Second click (click count = 2)
    down2 = CGEventCreateMouseEvent(None, down_type, (x, y), btn_num)
    up2 = CGEventCreateMouseEvent(None, up_type, (x, y), btn_num)
    CGEventSetIntegerValueField(down2, kCGMouseEventClickState, 2)
    CGEventSetIntegerValueField(up2, kCGMouseEventClickState, 2)
    CGEventSetFlags(down2, 0)  # No modifier flags
    CGEventSetFlags(up2, 0)    # No modifier flags

    CGEventPost(kCGHIDEventTap, down2)
    CGEventPost(kCGHIDEventTap, up2)

    print("[double_click] Posted double-click event")

def scroll(vx, vy, scroll_multiplier):
    """
    Scroll the screen based on stick input.

    Args:
        vx: Horizontal velocity (-1 to 1, left to right)
        vy: Vertical velocity (-1 to 1, up to down)
        scroll_multiplier: Sensitivity multiplier from config
    """
    # Natural scroll: stick up = scroll up (negative dy), stick down = scroll down (positive dy)
    # Horizontal: stick right = scroll left (negative dx), stick left = scroll right (positive dx) [reversed for intuitive feel]
    scroll_y = -int(vy * scroll_multiplier)  # Negative for natural scroll
    scroll_x = -int(vx * scroll_multiplier)  # Negative for intuitive horizontal scroll

    if scroll_y != 0 or scroll_x != 0:
        # kCGScrollEventUnitLine = 1
        ev = CGEventCreateScrollWheelEvent(None, 1, 2, scroll_y, scroll_x)
        CGEventSetFlags(ev, 0)  # Clear modifier flags
        CGEventPost(kCGHIDEventTap, ev)

def start_drag():
    """Start mouse drag by holding left button down."""
    x, y = current_mouse_pos()
    ev = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, (x, y), 0)
    CGEventSetFlags(ev, 0)  # Clear modifier flags
    CGEventPost(kCGHIDEventTap, ev)

def end_drag():
    """End mouse drag by releasing left button."""
    x, y = current_mouse_pos()
    ev = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, (x, y), 0)
    CGEventSetFlags(ev, 0)  # Clear modifier flags
    CGEventPost(kCGHIDEventTap, ev)

def drag_move(x, y):
    """Move cursor while dragging."""
    ev = CGEventCreateMouseEvent(None, kCGEventLeftMouseDragged, (x, y), 0)
    CGEventSetFlags(ev, 0)  # Clear modifier flags
    CGEventPost(kCGHIDEventTap, ev)

def press_key(key_name):
    """Simulate a keyboard key press."""
    key_name = key_name.lower()
    print(f"[press_key] Attempting to press key: {key_name}")

    if key_name in KEY_CODES:
        keycode = KEY_CODES[key_name]
        print(f"[press_key] Found keycode {keycode} for '{key_name}'")
        ev_down = CGEventCreateKeyboardEvent(None, keycode, True)
        ev_up = CGEventCreateKeyboardEvent(None, keycode, False)
        CGEventPost(kCGHIDEventTap, ev_down)
        CGEventPost(kCGHIDEventTap, ev_up)
        print(f"[press_key] ✓ Key '{key_name}' posted")
    else:
        print(f"[press_key] ⚠️  Warning: Unknown key '{key_name}'")

def press_key_with_modifier(key_name, modifier_flags=0):
    """
    Simulate a keyboard key press with modifiers.

    Args:
        key_name: Key to press
        modifier_flags: Modifier flags (e.g., kCGEventFlagMaskCommand for Cmd)
    """
    key_name = key_name.lower()
    if key_name in KEY_CODES:
        keycode = KEY_CODES[key_name]
        ev_down = CGEventCreateKeyboardEvent(None, keycode, True)
        ev_up = CGEventCreateKeyboardEvent(None, keycode, False)

        if modifier_flags:
            CGEventSetFlags(ev_down, modifier_flags)
            CGEventSetFlags(ev_up, modifier_flags)

        CGEventPost(kCGHIDEventTap, ev_down)
        CGEventPost(kCGHIDEventTap, ev_up)
    else:
        print(f"Warning: Unknown key '{key_name}'")

def zoom_in():
    """Zoom in using Cmd + Shift + ; (produces Cmd + +)"""
    print("[zoom_in] Attempting zoom in with Cmd+Shift+; (Cmd++)...")

    keycode = 41  # ';' key (Shift+; produces '+' on user's keyboard)
    ev_down = CGEventCreateKeyboardEvent(None, keycode, True)
    ev_up = CGEventCreateKeyboardEvent(None, keycode, False)

    # Use Command + Shift to produce Cmd + +
    CGEventSetFlags(ev_down, kCGEventFlagMaskCommand | kCGEventFlagMaskShift)
    CGEventSetFlags(ev_up, kCGEventFlagMaskCommand | kCGEventFlagMaskShift)

    CGEventPost(kCGHIDEventTap, ev_down)
    time.sleep(0.03)
    CGEventPost(kCGHIDEventTap, ev_up)

    print("[zoom_in] ✓ Zoom in event posted (Cmd++)")

def zoom_out():
    """Zoom out using Cmd + -"""
    print("[zoom_out] Attempting zoom out with Cmd+-...")

    keycode = 27  # '-' key
    ev_down = CGEventCreateKeyboardEvent(None, keycode, True)
    ev_up = CGEventCreateKeyboardEvent(None, keycode, False)
    CGEventSetFlags(ev_down, kCGEventFlagMaskCommand)
    CGEventSetFlags(ev_up, kCGEventFlagMaskCommand)
    CGEventPost(kCGHIDEventTap, ev_down)
    time.sleep(0.03)
    CGEventPost(kCGHIDEventTap, ev_up)

    print("[zoom_out] ✓ Zoom out event posted")

def clear_modifier_keys():
    """Explicitly clear modifier key state by posting key-up events for Cmd and Shift (both left and right)."""
    # macOS key codes:
    # Cmd: left=55, right=54
    # Shift: left=56, right=60

    modifier_keycodes = [55, 54, 56, 60]  # left-Cmd, right-Cmd, left-Shift, right-Shift

    for keycode in modifier_keycodes:
        ev_up = CGEventCreateKeyboardEvent(None, keycode, False)
        CGEventPost(kCGHIDEventTap, ev_up)

    print("[clear_modifiers] ✓ Cleared Cmd and Shift modifier keys (left+right)")

def write_button_state(a, b, x, y, plus, r, zr, mode, last_action):
    """Write current button state to shared file for GUI."""
    button_states = {
        "A": a,
        "B": b,
        "X": x,
        "Y": y,
        "+": plus,
        "R": r,
        "ZR": zr
    }
    shared_state.write_state(button_states, mode, last_action)

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

# Byte 2 masks
PLUS_MASK = 0x02
R_MASK = 0x40
ZR_MASK = 0x80

# Load configuration
config = load_config()
if config and "speed" in config:
    TICK = 1 / config["speed"]["tick_hz"]
    STEP_MIN = config["speed"]["step_min"]
    STEP_MAX = config["speed"]["step_max"]
    RAMP_SEC = config["speed"]["ramp_sec"]
    DOUBLE_CLICK_WINDOW = config["speed"].get("double_click_ms", 350) / 1000.0  # Convert ms to seconds
else:
    # Default values
    TICK = 1/120
    STEP_MIN = 5
    STEP_MAX = 20
    RAMP_SEC = 0.7
    DOUBLE_CLICK_WINDOW = 0.35  # Default: 350ms

# Drag arming delay to prevent unwanted clicks during zoom combos
DRAG_ARM_DELAY = 0.12  # 120ms delay before starting drag (prevents click during zoom)
DRAG_ARM_MOVEMENT_THRESHOLD = 0.1  # Require minimal stick movement to confirm drag intent

# Get screen dimensions for boundary checking
SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_dimensions()
print(f"Screen dimensions: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
print(f"Double-click window: {DOUBLE_CLICK_WINDOW*1000:.0f}ms")
print("Version: v2.1-fixed (zoom & escape debug)")
print("\n⚠️  IMPORTANT: Ensure Accessibility permissions are granted!")
print("   System Settings → Privacy & Security → Accessibility")
print("   Add your terminal app (Terminal.app or iTerm.app)\n")

info = find_joycon_r()
if info is None:
    sys.exit(1)

dev = hid.Device(path=info["path"])
dev.nonblocking = True   # ★ここがあなたの環境では正解

print(f"Opened {info.get('product_string')}  VID={info['vendor_id']:04x} PID={info['product_id']:04x}")
print("Joy-Con (R) Controls:")
print("  Stick: Move cursor | A: Left click (double-tap for double-click) | X: Right click")
print("  B: Right arrow | Y: Left arrow | +: ESC")
print("  R + Stick: Scroll | ZR + Stick: Drag | ZR + X/B: Zoom in/out")
print("Press Ctrl+C to stop")

def handle_button(button_name, is_pressed, was_pressed, zr_held=False):
    """Handle button press based on config.

    Args:
        button_name: Name of the button (A, B, X, Y, +)
        is_pressed: Current state of button
        was_pressed: Previous state of button
        zr_held: Whether ZR is currently held (for zoom combo detection)
    """
    if is_pressed and not was_pressed:  # Button just pressed
        # Skip X/B handlers during zoom combos (ZR held)
        if zr_held and button_name in ["X", "B"]:
            print(f"[{button_name}] Skipped (zoom combo active)")
            return

        print(f"[{button_name}] Button pressed (mode={current_mode}), checking config...")

        if config and "buttons" in config:
            btn_config = config["buttons"].get(button_name, {})
            action = btn_config.get("action")
            value = btn_config.get("value")

            print(f"[{button_name}] Config found - action={action}, value={value}")

            if action == "mouse_click" and value:
                click(value)
            elif action == "keyboard" and value:
                print(f"[{button_name}] Calling press_key({value})")
                press_key(value)
        else:
            print(f"[{button_name}] No config loaded, using default behavior")
            # Default behavior
            if button_name == "A":
                click("left")
            elif button_name == "B":
                click("right")

vx = vy = 0
moving_since = None
last_a = last_b = last_x = last_y = last_plus = last_r = last_zr = False
is_dragging = False
current_mode = "normal"  # Track current mode: zoom/drag/scroll/normal

# Drag arming state
pending_drag = False  # ZR pressed but drag not yet started
pending_drag_time = 0.0  # When ZR was pressed

# Double-click state machine for A button
# States: "idle", "waiting_for_second"
a_click_state = "idle"
a_first_click_time = 0.0

next_tick = time.perf_counter()

try:
    while True:
        data = dev.read(64)
        if data:
            b = bytes(data)
            if len(b) >= 4:
                btn1 = b[1]
                btn2 = b[2]  # Read byte 2 for R, ZR, +
                hat  = b[3]

                vx, vy = HAT_TO_VEC.get(hat, (0, 0))
                if vx or vy:
                    if moving_since is None:
                        moving_since = time.perf_counter()
                else:
                    moving_since = None

                # Extract button states
                a_now = (btn1 & A_MASK) != 0
                b_now = (btn1 & B_MASK) != 0
                x_now = (btn1 & X_MASK) != 0
                y_now = (btn1 & Y_MASK) != 0
                plus_now = (btn2 & PLUS_MASK) != 0
                r_now = (btn2 & R_MASK) != 0
                zr_now = (btn2 & ZR_MASK) != 0

                # Debug drag state on ZR/X/B changes (only log on change)
                if (zr_now != last_zr) or (x_now != last_x) or (b_now != last_b):
                    zoom_combo_check = zr_now and (x_now or b_now)
                    print(f"[drag-state] zr={zr_now} x={x_now} b={b_now} | pending={pending_drag} active={is_dragging} | zoom_combo={zoom_combo_check}")

                # Debug Plus button state changes
                if plus_now != last_plus:
                    print(f"[+] Button state changed: {last_plus} -> {plus_now} (byte2=0x{btn2:02x})")

                # === Mode Priority Logic ===
                # Priority: ZR+X/B > ZR (drag) > R (scroll) > Normal

                # 1. HIGHEST PRIORITY: ZR + X (zoom in) or ZR + B (zoom out)
                # Initialize handler blocking flags
                handled_x = False
                handled_b = False

                if zr_now:
                    if x_now and not last_x:
                        zoom_in()
                        clear_modifier_keys()  # Clear lingering modifier state
                        handled_x = True  # Mark X as consumed
                        print(f"[zoom] ✓ Zoom IN (ZR+X) - mode=zoom, handled_x=True")
                        write_button_state(a_now, b_now, x_now, y_now, plus_now, r_now, zr_now,
                                          "zoom", "Zoom IN (ZR+X)")
                    if b_now and not last_b:
                        zoom_out()
                        clear_modifier_keys()  # Clear lingering modifier state
                        handled_b = True  # Mark B as consumed
                        print(f"[zoom] ✓ Zoom OUT (ZR+B) - mode=zoom, handled_b=True")
                        write_button_state(a_now, b_now, x_now, y_now, plus_now, r_now, zr_now,
                                          "zoom", "Zoom OUT (ZR+B)")

                    # Skip other X/B actions when ZR is held (but not if already handled by zoom)
                    if not handled_x:
                        handled_x = x_now  # Still block during non-zoom ZR usage
                    if not handled_b:
                        handled_b = b_now  # Still block during non-zoom ZR usage

                # 2. Handle regular button presses (not in zoom mode)
                if not handled_x:
                    handle_button("X", x_now, last_x, zr_now)
                if not handled_b:
                    handle_button("B", b_now, last_b, zr_now)

                # === A Button with Double-Click Detection ===
                # Check for A button rising edge
                if a_now and not last_a:  # A button just pressed
                    now_time = time.perf_counter()
                    if a_click_state == "idle":
                        # First click detected - wait for potential second click
                        print(f"[A] First press detected, waiting for second...")
                        a_click_state = "waiting_for_second"
                        a_first_click_time = now_time
                    elif a_click_state == "waiting_for_second":
                        # Second click detected - check if within window
                        time_diff = now_time - a_first_click_time
                        print(f"[A] Second press detected, time diff: {time_diff*1000:.0f}ms")
                        if time_diff <= DOUBLE_CLICK_WINDOW:
                            # Double-click confirmed!
                            print("[A] DOUBLE-CLICK!")
                            double_click("left")
                            a_click_state = "idle"
                        else:
                            # Too late - this is a new first click
                            # Execute the delayed single click for the old press
                            print(f"[A] Too late ({time_diff*1000:.0f}ms > {DOUBLE_CLICK_WINDOW*1000:.0f}ms), single click")
                            click("left")
                            # Start waiting for second click again
                            a_click_state = "waiting_for_second"
                            a_first_click_time = now_time

                handle_button("Y", y_now, last_y, zr_now)
                handle_button("+", plus_now, last_plus, False)  # Plus never affected by ZR

                # 3. Handle drag mode state transitions with ARM DELAY
                zoom_combo_now = zr_now and (x_now or b_now)

                if zoom_combo_now:
                    # Zoom combo detected - cancel any pending drag, end active drag
                    if pending_drag:
                        print("[drag] ✓ Cancelled pending drag (zoom combo detected)")
                        pending_drag = False
                    if is_dragging:
                        print("[drag] Force ending active drag during zoom combo")
                        end_drag()
                        is_dragging = False

                elif zr_now and not last_zr:
                    # ZR just pressed - ARM drag (don't start yet)
                    print(f"[drag] ZR pressed → ARMING drag (120ms delay)")
                    pending_drag = True
                    pending_drag_time = time.perf_counter()

                elif (not zr_now) and last_zr:
                    # ZR released
                    if pending_drag:
                        # ZR released before drag started - just cancel pending
                        print(f"[drag] ZR released before drag started - cancel pending")
                        pending_drag = False
                    if is_dragging:
                        # Drag was active - end it
                        print(f"[drag] Ending drag (ZR released)")
                        end_drag()
                        is_dragging = False

                # Determine current mode and log transitions
                zoom_combo_active = zr_now and (x_now or b_now)
                new_mode = "normal"

                if zoom_combo_active:
                    new_mode = "zoom"
                elif is_dragging:
                    new_mode = "drag"
                elif r_now and (vx or vy):
                    new_mode = "scroll"
                else:
                    new_mode = "normal"

                # Log mode changes
                if new_mode != current_mode:
                    print(f"[MODE] {current_mode} → {new_mode}")
                    current_mode = new_mode

                # Write state to shared file for GUI
                write_button_state(a_now, b_now, x_now, y_now, plus_now, r_now, zr_now,
                                  current_mode, f"Mode: {current_mode}")

                # Store button states
                last_a, last_b, last_x, last_y = a_now, b_now, x_now, y_now
                last_plus, last_r, last_zr = plus_now, r_now, zr_now

        now = time.perf_counter()
        if now >= next_tick:
            next_tick += TICK

            # Check for double-click timeout
            if a_click_state == "waiting_for_second":
                if (now - a_first_click_time) > DOUBLE_CLICK_WINDOW:
                    # Timeout - execute single click
                    print("[A] Timeout - executing single click")
                    click("left")
                    a_click_state = "idle"

            # Check if pending drag should be activated
            if pending_drag and not is_dragging:
                elapsed = now - pending_drag_time
                has_movement = (vx != 0 or vy != 0)

                if elapsed >= DRAG_ARM_DELAY and has_movement:
                    # Delay elapsed + stick movement confirmed → start drag
                    print(f"[drag] ✓ ARMED drag activated (delay: {elapsed*1000:.0f}ms, movement: vx={vx} vy={vy})")
                    start_drag()
                    is_dragging = True
                    pending_drag = False
                elif elapsed >= (DRAG_ARM_DELAY * 3):
                    # Timeout without movement - cancel
                    print(f"[drag] ✗ ARMED drag timeout (no movement in {elapsed*1000:.0f}ms)")
                    pending_drag = False

            if vx or vy:
                # Calculate movement parameters
                t = 0.0 if moving_since is None else (now - moving_since)
                alpha = min(max(t / RAMP_SEC, 0.0), 1.0)
                step = STEP_MIN + (STEP_MAX - STEP_MIN) * alpha

                # === Mode-based movement ===
                if is_dragging:
                    # DRAG MODE: Actively dragging (drag was properly started)
                    x, y = current_mouse_pos()
                    new_x = x + vx * step
                    new_y = y + vy * step
                    clamped_x, clamped_y = clamp_coordinates(new_x, new_y, SCREEN_WIDTH, SCREEN_HEIGHT)
                    drag_move(clamped_x, clamped_y)

                elif r_now:
                    # SCROLL MODE: R held
                    # Use scroll multiplier from config (default 10)
                    scroll_multiplier = config.get("speed", {}).get("scroll_multiplier", 10) if config else 10
                    scroll(vx, vy, scroll_multiplier)

                else:
                    # NORMAL MODE: Cursor movement
                    x, y = current_mouse_pos()
                    new_x = x + vx * step
                    new_y = y + vy * step
                    clamped_x, clamped_y = clamp_coordinates(new_x, new_y, SCREEN_WIDTH, SCREEN_HEIGHT)
                    post_move_abs(clamped_x, clamped_y)

        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    shared_state.clear_state()  # Clean up state file
    dev.close()
    print("\nclosed")