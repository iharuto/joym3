# joym3

## SetUp

```bash
brew install hidapi
/opt/homebrew/bin/python3 -m venv ~/joycon-venv
~/joycon-venv/bin/activate
pip install --upgrade pip
pip install hid pyobjc
```

then, connect joycon to mac via bluetooth. to see the succeeded connection, run

```bash
python - <<'PY'
import hid
hits=[]
for d in hid.enumerate():
    s=(d.get("product_string") or "")
    if "Joy-Con" in s or "Nintendo" in s:
        hits.append((hex(d["vendor_id"]), hex(d["product_id"]), s))
for h in hits:
    print(h)
print("count:", len(hits))
PY
```

output would be like

```bash
('0x57e', '0x2007', 'Joy-Con (R)')
count: 1
```

## Test


```bash
python - <<'PY'
import hid, time, sys

def find_joycon_r():
    hits = []
    for d in hid.enumerate():
        s = (d.get("product_string") or "")
        if s == "Joy-Con (R)":
            hits.append(d)

    if len(hits) == 0:
        print("Joy-Con (R) が見つかりませんでした")
        return None
    if len(hits) > 1:
        print("Joy-Con (R) が複数見つかりました（想定外）")
        for h in hits:
            print(f"VID={h['vendor_id']:04x} PID={h['product_id']:04x} path={h.get('path')}")
        return None

    return hits[0]

info = find_joycon_r()
if info is None:
    sys.exit(1)

dev = hid.Device(path=info["path"])  # VID/PIDをハードコーディングしない

print(f"Opened {info.get('product_string')}  VID={info['vendor_id']:04x} PID={info['product_id']:04x}")
print("Move stick / press buttons. Ctrl+C to stop.")

last = None
t0 = time.time()

try:
    while True:
        data = dev.read(64)
        if data:
            b = bytes(data)
            if b != last:
                last = b
                head = " ".join(f"{x:02x}" for x in b[:24])
                print(f"{time.time()-t0:8.3f}s  len={len(b):2d}  {head}")
        time.sleep(0.01)
except KeyboardInterrupt:
    pass
finally:
    dev.close()
    print("\nclosed")
PY
```

if you press buttons or tilt stick, you'll see this kind of table

```bash
Opened Joy-Con (R)  VID=057e PID=2007
Move stick / press buttons. Ctrl+C to stop.
   5.144s  len=12  3f 02 00 08 00 80 00 80 00 80 00 80 (Xを押した時)
   5.325s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (Xを押し終えた時)
   6.959s  len=12  3f 01 00 08 00 80 00 80 00 80 00 80 (Aを押した時)
   7.034s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (Aを押し終えた時)
   9.644s  len=12  3f 04 00 08 00 80 00 80 00 80 00 80 (Bを押した時)
   9.749s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (Bを押し終えた時)
  12.059s  len=12  3f 08 00 08 00 80 00 80 00 80 00 80 (Yを押した時)
  12.193s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (Yを押し終えた時)
  17.638s  len=12  3f 00 40 08 00 80 00 80 00 80 00 80 (Rを押した時)
  17.803s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (Rを押し終えた時)
  19.544s  len=12  3f 00 80 08 00 80 00 80 00 80 00 80 (ZRを押した時)
  19.679s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (ZRを押し終えた時)
  22.514s  len=12  3f 00 00 02 00 80 00 80 00 80 00 80 (↑スティックを押した時)
  22.784s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (↑スティックを押し終えた時)
  24.539s  len=12  3f 00 00 04 00 80 00 80 00 80 00 80 (→スティックを押した時)
  24.719s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (→スティックを押し終えた時)
  25.964s  len=12  3f 00 00 06 00 80 00 80 00 80 00 80 (↓スティックを押した時)
  26.143s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (↓スティックを押し終えた時)
  26.999s  len=12  3f 00 00 00 00 80 00 80 00 80 00 80 (←スティックを押した時)
  27.148s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (←スティックを押し終えた時)
  33.689s  len=12  3f 00 00 03 00 80 00 80 00 80 00 80 (スティックを右斜め上に押した時)
  33.869s  len=12  3f 00 00 08 00 80 00 80 00 80 00 80 (スティックを右斜め上に押しおえた時)
```


## Execution

```bash
python - <<'PY'
import hid, time, sys

from Quartz.CoreGraphics import (
    CGEventCreate, CGEventGetLocation,
    CGEventCreateMouseEvent, CGEventPost,
    kCGHIDEventTap, kCGEventMouseMoved,
    kCGEventLeftMouseDown, kCGEventLeftMouseUp,
    kCGEventRightMouseDown, kCGEventRightMouseUp,
)

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

vx = vy = 0
moving_since = None
last_a = last_b = False

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
                if a_now and not last_a:
                    click("left")
                if b_now and not last_b:
                    click("right")
                last_a, last_b = a_now, b_now

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
PY

```

