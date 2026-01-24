"""
Configuration management for Joy-Con GUI application.
Handles loading, saving, and validating configuration files.
"""

import json
import os
from typing import Dict, Any, Optional


def get_default_config() -> Dict[str, Any]:
    """Return the default configuration dictionary."""
    return {
        "speed": {
            "tick_hz": 120,
            "step_min": 5,
            "step_max": 20,
            "ramp_sec": 0.7
        },
        "buttons": {
            "A": {"action": "mouse_click", "value": "left"},
            "B": {"action": "mouse_click", "value": "right"},
            "X": {"action": "keyboard", "value": "space"},
            "Y": {"action": "keyboard", "value": "escape"},
            "R": {"action": "none", "value": None},
            "ZR": {"action": "none", "value": None}
        }
    }


def load_config(path: str) -> Optional[Dict[str, Any]]:
    """
    Load configuration from a JSON file.

    Args:
        path: Path to the configuration file

    Returns:
        Configuration dictionary or None if file doesn't exist or is invalid
    """
    if not os.path.exists(path):
        return None

    try:
        with open(path, 'r') as f:
            config = json.load(f)
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config from {path}: {e}")
        return None


def save_config(path: str, config: Dict[str, Any]) -> bool:
    """
    Save configuration to a JSON file.

    Args:
        path: Path to save the configuration file
        config: Configuration dictionary to save

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving config to {path}: {e}")
        return False


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate that a configuration has valid values.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(config, dict):
        return False

    # Validate speed settings
    if "speed" in config:
        speed = config["speed"]
        if not isinstance(speed, dict):
            return False

        # Check tick_hz
        if "tick_hz" in speed:
            tick_hz = speed["tick_hz"]
            if not isinstance(tick_hz, (int, float)) or tick_hz < 30 or tick_hz > 240:
                return False

        # Check step_min
        if "step_min" in speed:
            step_min = speed["step_min"]
            if not isinstance(step_min, (int, float)) or step_min < 1 or step_min > 50:
                return False

        # Check step_max
        if "step_max" in speed:
            step_max = speed["step_max"]
            if not isinstance(step_max, (int, float)) or step_max < 1 or step_max > 50:
                return False

        # Check ramp_sec
        if "ramp_sec" in speed:
            ramp_sec = speed["ramp_sec"]
            if not isinstance(ramp_sec, (int, float)) or ramp_sec < 0.1 or ramp_sec > 2.0:
                return False

    # Validate button settings
    if "buttons" in config:
        buttons = config["buttons"]
        if not isinstance(buttons, dict):
            return False

        valid_actions = ["mouse_click", "keyboard", "none"]
        valid_mouse_values = ["left", "right"]

        for button_name, button_config in buttons.items():
            if not isinstance(button_config, dict):
                return False

            action = button_config.get("action")
            value = button_config.get("value")

            if action not in valid_actions:
                return False

            if action == "mouse_click" and value not in valid_mouse_values:
                return False

            if action == "keyboard" and not (value is None or isinstance(value, str)):
                return False

    return True
