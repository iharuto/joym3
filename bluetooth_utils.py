"""
Bluetooth utilities for Joy-Con detection and connection testing.
"""

import hid
from typing import List, Dict, Optional


def scan_joycon_devices() -> List[Dict]:
    """
    Scan for all Joy-Con devices connected via Bluetooth/HID.

    Returns:
        List of device info dictionaries with keys: vendor_id, product_id,
        product_string, path
    """
    try:
        devices = hid.enumerate()
        joycon_devices = []

        for device in devices:
            product_string = device.get("product_string", "")
            # Look for both Joy-Con (R) and Joy-Con (L)
            if "Joy-Con" in product_string:
                joycon_devices.append({
                    "vendor_id": device.get("vendor_id"),
                    "product_id": device.get("product_id"),
                    "product_string": product_string,
                    "path": device.get("path"),
                    "serial_number": device.get("serial_number", ""),
                    "manufacturer_string": device.get("manufacturer_string", "")
                })

        return joycon_devices
    except Exception as e:
        print(f"Error scanning for Joy-Con devices: {e}")
        return []


def find_joycon_r() -> Optional[Dict]:
    """
    Find a single Joy-Con (R) device.

    Returns:
        Device info dictionary or None if not found or multiple found
    """
    hits = [d for d in hid.enumerate() if (d.get("product_string") or "") == "Joy-Con (R)"]

    if len(hits) == 0:
        print("Joy-Con (R) が見つかりませんでした")
        return None

    if len(hits) > 1:
        print("Joy-Con (R) が複数見つかりました（想定外）")
        for h in hits:
            print(f"VID={h['vendor_id']:04x} PID={h['product_id']:04x} path={h.get('path')}")
        return None

    return hits[0]


def format_device_info(device: Dict) -> str:
    """
    Format device information for display in GUI.

    Args:
        device: Device info dictionary

    Returns:
        Formatted string with device details
    """
    product = device.get("product_string", "Unknown")
    vendor_id = device.get("vendor_id", 0)
    product_id = device.get("product_id", 0)
    serial = device.get("serial_number", "N/A")

    return f"{product} (VID:{vendor_id:04x} PID:{product_id:04x}) Serial: {serial}"


def test_connection(device_path: bytes) -> bool:
    """
    Test if a device can be opened and communicated with.

    Args:
        device_path: Device path from HID enumeration

    Returns:
        True if device can be opened, False otherwise
    """
    try:
        dev = hid.Device(path=device_path)
        dev.close()
        return True
    except Exception as e:
        print(f"Failed to open device: {e}")
        return False
