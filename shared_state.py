"""
Shared state module for communicating between control_cursor.py and GUI.
Uses a JSON file for simple IPC.
"""
import json
import os
import time
from pathlib import Path

STATE_FILE = "/Users/haruto/joym3/joycon_state.json"

def write_state(button_states, mode, last_action):
    """
    Write current Joy-Con state to shared file.

    Args:
        button_states: Dict of button names to boolean states
        mode: Current mode string ("normal", "zoom", "drag", "scroll")
        last_action: String describing last action performed
    """
    state = {
        "buttons": button_states,
        "mode": mode,
        "last_action": last_action,
        "timestamp": time.time()
    }

    try:
        # Write atomically using temp file
        temp_file = STATE_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(state, f)
        os.replace(temp_file, STATE_FILE)
    except Exception as e:
        # Silently fail - don't crash cursor control
        pass

def read_state():
    """
    Read current Joy-Con state from shared file.

    Returns:
        Dict with keys: buttons, mode, last_action, timestamp
        Returns None if file doesn't exist or is invalid
    """
    try:
        if not os.path.exists(STATE_FILE):
            return None

        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def clear_state():
    """Remove state file."""
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    except Exception:
        pass
