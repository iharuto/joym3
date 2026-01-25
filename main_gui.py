"""
Joy-Con GUI Application
Main GUI interface for configuring and controlling Joy-Con cursor control.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import time
import config_manager
import bluetooth_utils
import shared_state


class JoyConGUI:
    """Main GUI application for Joy-Con cursor control."""

    def __init__(self, root):
        self.root = root
        self.root.title("Joy-Con Cursor Control")
        self.root.geometry("600x500")

        # Configuration paths
        self.config_dir = "/Users/haruto/joym3/config"
        self.runtime_config_path = os.path.join(self.config_dir, "runtime_config.json")
        self.default_config_path = os.path.join(self.config_dir, "default_config.json")
        self.profiles_dir = os.path.join(self.config_dir, "profiles")

        # Python interpreter and script paths
        self.python_path = "/Users/haruto/joym3/joycon-venv/bin/python"
        self.cursor_script = "/Users/haruto/joym3/control_cursor.py"

        # Subprocess for cursor control
        self.cursor_process = None

        # Load or create configuration
        self.config = self.load_or_create_config()

        # Create GUI
        self.create_tabs()

        # Setup close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_or_create_config(self):
        """Load configuration or create default if it doesn't exist."""
        config = config_manager.load_config(self.runtime_config_path)
        if config is None:
            # Try loading default config
            config = config_manager.load_config(self.default_config_path)
            if config is None:
                # Use built-in default
                config = config_manager.get_default_config()
            # Save as runtime config
            config_manager.save_config(self.runtime_config_path, config)
        return config

    def create_tabs(self):
        """Create the tabbed interface."""
        # Create notebook (tab container)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.connection_tab = ttk.Frame(self.notebook)
        self.speed_tab = ttk.Frame(self.notebook)
        self.button_tab = ttk.Frame(self.notebook)
        self.status_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.connection_tab, text="Connection")
        self.notebook.add(self.speed_tab, text="Speed Control")
        self.notebook.add(self.button_tab, text="Button Customization")
        self.notebook.add(self.status_tab, text="Live Status")

        # Setup each tab
        self.setup_connection_tab()
        self.setup_speed_tab()
        self.setup_button_tab()
        self.setup_status_tab()

    def setup_connection_tab(self):
        """Setup the connection tab UI."""
        # Title
        title = ttk.Label(self.connection_tab, text="Joy-Con Device Connection",
                         font=("Helvetica", 14, "bold"))
        title.pack(pady=10)

        # Device list frame
        list_frame = ttk.LabelFrame(self.connection_tab, text="Detected Devices", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Scrollbar and listbox
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.device_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.device_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.device_listbox.yview)

        # Scan button
        scan_btn = ttk.Button(list_frame, text="Scan for Joy-Con Devices", command=self.scan_devices)
        scan_btn.pack(pady=5)

        # Status frame
        status_frame = ttk.Frame(self.connection_tab)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Button frame
        button_frame = ttk.Frame(self.connection_tab)
        button_frame.pack(pady=10)

        self.connect_btn = ttk.Button(button_frame, text="Allow control", command=self.connect_device)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_device, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Store device list
        self.devices = []

        # Initial scan
        self.scan_devices()

    def scan_devices(self):
        """Scan for Joy-Con devices."""
        self.device_listbox.delete(0, tk.END)
        self.devices = bluetooth_utils.scan_joycon_devices()

        if not self.devices:
            self.device_listbox.insert(tk.END, "No Joy-Con devices found")
        else:
            for device in self.devices:
                display_text = bluetooth_utils.format_device_info(device)
                self.device_listbox.insert(tk.END, display_text)

    def connect_device(self):
        """Connect to Joy-Con and start cursor control."""
        # Check if a device is selected
        selection = self.device_listbox.curselection()
        if not selection and self.devices:
            # If no selection but devices exist, use first device
            self.device_listbox.selection_set(0)
        elif not self.devices:
            messagebox.showwarning("Warning", "No Joy-Con devices detected. Please scan first.")
            return

        # Launch cursor control
        if self.launch_cursor_control():
            self.status_label.config(text="Connected", foreground="green")
            self.connect_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

    def stop_device(self):
        """Stop cursor control."""
        self.stop_cursor_control()
        self.status_label.config(text="Disconnected", foreground="red")
        self.connect_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        # Clear status display
        shared_state.clear_state()

    def setup_speed_tab(self):
        """Setup the speed control tab UI."""
        # Title
        title = ttk.Label(self.speed_tab, text="Cursor Speed Settings",
                         font=("Helvetica", 14, "bold"))
        title.pack(pady=10)

        # Create frame for settings
        settings_frame = ttk.Frame(self.speed_tab)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # Minimum Speed
        min_frame = ttk.LabelFrame(settings_frame, text="Minimum Speed (pixels)", padding=10)
        min_frame.pack(fill=tk.X, pady=10)

        self.step_min_var = tk.IntVar(value=self.config["speed"]["step_min"])
        self.step_min_label = ttk.Label(min_frame, text=str(self.step_min_var.get()))
        self.step_min_label.pack()

        step_min_scale = ttk.Scale(min_frame, from_=1, to=50, orient=tk.HORIZONTAL,
                                   variable=self.step_min_var,
                                   command=lambda v: self.step_min_label.config(text=str(int(float(v)))))
        step_min_scale.pack(fill=tk.X)

        # Maximum Speed
        max_frame = ttk.LabelFrame(settings_frame, text="Maximum Speed (pixels)", padding=10)
        max_frame.pack(fill=tk.X, pady=10)

        self.step_max_var = tk.IntVar(value=self.config["speed"]["step_max"])
        self.step_max_label = ttk.Label(max_frame, text=str(self.step_max_var.get()))
        self.step_max_label.pack()

        step_max_scale = ttk.Scale(max_frame, from_=1, to=50, orient=tk.HORIZONTAL,
                                   variable=self.step_max_var,
                                   command=lambda v: self.step_max_label.config(text=str(int(float(v)))))
        step_max_scale.pack(fill=tk.X)

        # Acceleration Ramp
        ramp_frame = ttk.LabelFrame(settings_frame, text="Acceleration Ramp (seconds)", padding=10)
        ramp_frame.pack(fill=tk.X, pady=10)

        self.ramp_sec_var = tk.DoubleVar(value=self.config["speed"]["ramp_sec"])
        self.ramp_sec_label = ttk.Label(ramp_frame, text=f"{self.ramp_sec_var.get():.2f}")
        self.ramp_sec_label.pack()

        ramp_scale = ttk.Scale(ramp_frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL,
                              variable=self.ramp_sec_var,
                              command=lambda v: self.ramp_sec_label.config(text=f"{float(v):.2f}"))
        ramp_scale.pack(fill=tk.X)

        # Polling Rate
        poll_frame = ttk.LabelFrame(settings_frame, text="Polling Rate (Hz)", padding=10)
        poll_frame.pack(fill=tk.X, pady=10)

        poll_inner = ttk.Frame(poll_frame)
        poll_inner.pack()

        ttk.Label(poll_inner, text="Polling Rate:").pack(side=tk.LEFT, padx=5)
        self.tick_hz_var = tk.IntVar(value=self.config["speed"]["tick_hz"])
        tick_spinbox = ttk.Spinbox(poll_inner, from_=30, to=240, textvariable=self.tick_hz_var, width=10)
        tick_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(poll_inner, text="Hz").pack(side=tk.LEFT)

        # Scroll Speed
        scroll_frame = ttk.LabelFrame(settings_frame, text="Scroll Speed (R + Stick)", padding=10)
        scroll_frame.pack(fill=tk.X, pady=10)

        scroll_multiplier = self.config["speed"].get("scroll_multiplier", 10)
        self.scroll_multiplier_var = tk.IntVar(value=scroll_multiplier)
        self.scroll_multiplier_label = ttk.Label(scroll_frame, text=str(self.scroll_multiplier_var.get()))
        self.scroll_multiplier_label.pack()

        scroll_scale = ttk.Scale(scroll_frame, from_=1, to=50, orient=tk.HORIZONTAL,
                                variable=self.scroll_multiplier_var,
                                command=lambda v: self.scroll_multiplier_label.config(text=str(int(float(v)))))
        scroll_scale.pack(fill=tk.X)

        # Double-Click Timing
        double_click_frame = ttk.LabelFrame(settings_frame, text="Double-Click Timing", padding=10)
        double_click_frame.pack(fill=tk.X, pady=10)

        double_click_inner = ttk.Frame(double_click_frame)
        double_click_inner.pack()

        ttk.Label(double_click_inner, text="Max delay between clicks:").pack(side=tk.LEFT, padx=5)

        self.double_click_ms_var = tk.IntVar(value=self.config["speed"].get("double_click_ms", 250))
        double_click_combo = ttk.Combobox(
            double_click_inner,
            textvariable=self.double_click_ms_var,
            values=[200, 250, 300, 350, 400, 450, 500],
            state="readonly",
            width=8
        )
        double_click_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(double_click_inner, text="ms").pack(side=tk.LEFT)

        # Apply button
        apply_btn = ttk.Button(settings_frame, text="Apply Settings", command=self.apply_speed_settings)
        apply_btn.pack(pady=20)

    def apply_speed_settings(self):
        """Apply speed settings to configuration."""
        # Update config
        self.config["speed"]["step_min"] = self.step_min_var.get()
        self.config["speed"]["step_max"] = self.step_max_var.get()
        self.config["speed"]["ramp_sec"] = round(self.ramp_sec_var.get(), 2)
        self.config["speed"]["tick_hz"] = self.tick_hz_var.get()
        self.config["speed"]["scroll_multiplier"] = self.scroll_multiplier_var.get()
        self.config["speed"]["double_click_ms"] = self.double_click_ms_var.get()

        # Validate config
        if not config_manager.validate_config(self.config):
            messagebox.showerror("Error", "Invalid configuration values!")
            return

        # Save config
        if config_manager.save_config(self.runtime_config_path, self.config):
            messagebox.showinfo("Success", "Speed settings applied successfully!")

            # Restart cursor control if it's running
            if self.cursor_process is not None:
                if messagebox.askyesno("Restart Required",
                                      "Cursor control needs to be restarted for changes to take effect. Restart now?"):
                    self.restart_cursor_control()
        else:
            messagebox.showerror("Error", "Failed to save configuration!")

    def setup_button_tab(self):
        """Setup the button customization tab UI."""
        # Title
        title = ttk.Label(self.button_tab, text="Button Customization",
                         font=("Helvetica", 14, "bold"))
        title.pack(pady=10)

        # Create frame for button mappings
        mappings_frame = ttk.LabelFrame(self.button_tab, text="Button Mappings", padding=10)
        mappings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Button names
        buttons = ["A", "B", "X", "Y", "+", "R", "ZR"]

        # Store widgets
        self.button_action_vars = {}
        self.button_value_vars = {}

        # Create row for each button
        for i, button_name in enumerate(buttons):
            row_frame = ttk.Frame(mappings_frame)
            row_frame.pack(fill=tk.X, pady=5)

            # Button label
            ttk.Label(row_frame, text=f"{button_name}:", width=5).pack(side=tk.LEFT, padx=5)

            # Action combobox
            action_var = tk.StringVar()
            btn_config = self.config["buttons"].get(button_name, {"action": "none", "value": None})

            # Map action to display text
            action_map = {
                "mouse_click": "Mouse Click",
                "keyboard": "Keyboard",
                "none": "None"
            }
            action_var.set(action_map.get(btn_config["action"], "None"))

            action_combo = ttk.Combobox(row_frame, textvariable=action_var,
                                       values=["Mouse Click", "Keyboard", "None"],
                                       state="readonly", width=15)
            action_combo.pack(side=tk.LEFT, padx=5)
            self.button_action_vars[button_name] = action_var

            # Value entry
            value_var = tk.StringVar(value=btn_config["value"] or "")
            value_entry = ttk.Entry(row_frame, textvariable=value_var, width=15)
            value_entry.pack(side=tk.LEFT, padx=5)
            self.button_value_vars[button_name] = value_var

            # Help text
            help_text = "(left/right for mouse, key name for keyboard)"
            ttk.Label(row_frame, text=help_text, font=("Helvetica", 8), foreground="gray").pack(side=tk.LEFT, padx=5)

        # Mode information frame
        info_frame = ttk.LabelFrame(self.button_tab, text="Mode Operations", padding=10)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        info_text = """Special Modes (hold button + stick):
• R + Stick: Scroll mode
• ZR + Stick: Drag mode (mouse drag)
• ZR + X: Zoom in (Cmd + +)
• ZR + B: Zoom out (Cmd + -)

Note: R and ZR buttons are used for modes and cannot be customized."""
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, font=("Helvetica", 9))
        info_label.pack()

        # Profile management frame
        profile_frame = ttk.LabelFrame(self.button_tab, text="Profile Management", padding=10)
        profile_frame.pack(fill=tk.X, padx=20, pady=10)

        # Profile name entry and save button
        save_frame = ttk.Frame(profile_frame)
        save_frame.pack(fill=tk.X, pady=5)

        ttk.Label(save_frame, text="Profile Name:").pack(side=tk.LEFT, padx=5)
        self.profile_name_var = tk.StringVar(value="my_profile")
        ttk.Entry(save_frame, textvariable=self.profile_name_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_frame, text="Save Profile", command=self.save_profile).pack(side=tk.LEFT, padx=5)

        # Load profile combobox and button
        load_frame = ttk.Frame(profile_frame)
        load_frame.pack(fill=tk.X, pady=5)

        ttk.Label(load_frame, text="Load Profile:").pack(side=tk.LEFT, padx=5)
        self.profile_list_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(load_frame, textvariable=self.profile_list_var,
                                         state="readonly", width=20)
        self.profile_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(load_frame, text="Load", command=self.load_profile).pack(side=tk.LEFT, padx=5)

        # Refresh profile list
        self.refresh_profile_list()

        # Apply button
        apply_btn = ttk.Button(self.button_tab, text="Apply Button Settings", command=self.apply_button_settings)
        apply_btn.pack(pady=10)

    def setup_status_tab(self):
        """Setup the live status monitoring tab."""
        # Title
        title = ttk.Label(self.status_tab, text="Live Button Status",
                         font=("Helvetica", 14, "bold"))
        title.pack(pady=10)

        # Button status frame
        button_frame = ttk.LabelFrame(self.status_tab, text="Button States", padding=20)
        button_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create button status labels
        self.button_status_labels = {}
        buttons = ["A", "B", "X", "Y", "+", "R", "ZR"]

        # Create 2 rows of buttons
        row1_frame = ttk.Frame(button_frame)
        row1_frame.pack(pady=10)

        row2_frame = ttk.Frame(button_frame)
        row2_frame.pack(pady=10)

        for i, button_name in enumerate(buttons):
            parent = row1_frame if i < 4 else row2_frame

            btn_frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=2)
            btn_frame.pack(side=tk.LEFT, padx=10, pady=5)

            # Button name
            ttk.Label(btn_frame, text=button_name, font=("Helvetica", 12, "bold")).pack(pady=5)

            # Status label
            status_label = ttk.Label(btn_frame, text="Released",
                                    font=("Helvetica", 10),
                                    background="lightgray",
                                    foreground="black",
                                    width=10)
            status_label.pack(pady=5, padx=10)

            self.button_status_labels[button_name] = status_label

        # Mode display frame
        mode_frame = ttk.LabelFrame(self.status_tab, text="Current Mode", padding=20)
        mode_frame.pack(fill=tk.X, padx=20, pady=10)

        self.mode_label = ttk.Label(mode_frame, text="NORMAL",
                                    font=("Helvetica", 16, "bold"),
                                    foreground="blue")
        self.mode_label.pack(pady=10)

        # Last action frame
        action_frame = ttk.LabelFrame(self.status_tab, text="Last Action", padding=20)
        action_frame.pack(fill=tk.X, padx=20, pady=10)

        self.last_action_label = ttk.Label(action_frame, text="No action yet",
                                           font=("Helvetica", 10),
                                           wraplength=500)
        self.last_action_label.pack(pady=10)

        # Connection status
        self.connection_status_label = ttk.Label(self.status_tab,
                                                 text="⚠️ Not connected - start cursor control to see live status",
                                                 font=("Helvetica", 10),
                                                 foreground="red")
        self.connection_status_label.pack(pady=10)

        # Start polling
        self.poll_button_state()

    def poll_button_state(self):
        """Poll the shared state file and update button status display."""
        state = shared_state.read_state()

        if state and self.cursor_process is not None:
            # Update connection status
            self.connection_status_label.config(
                text="✓ Connected - showing live status",
                foreground="green"
            )

            # Update button states
            buttons = state.get("buttons", {})
            for button_name, is_pressed in buttons.items():
                if button_name in self.button_status_labels:
                    label = self.button_status_labels[button_name]
                    if is_pressed:
                        label.config(text="PRESSED", background="lightgreen", foreground="darkgreen")
                    else:
                        label.config(text="Released", background="lightgray", foreground="black")

            # Update mode
            mode = state.get("mode", "unknown").upper()
            mode_colors = {
                "NORMAL": "blue",
                "ZOOM": "green",
                "DRAG": "orange",
                "SCROLL": "purple"
            }
            self.mode_label.config(text=mode, foreground=mode_colors.get(mode, "black"))

            # Update last action
            last_action = state.get("last_action", "No action")
            timestamp = state.get("timestamp", 0)
            age = time.time() - timestamp
            self.last_action_label.config(text=f"{last_action} ({age:.1f}s ago)")
        else:
            # No state or not connected
            if self.cursor_process is None:
                self.connection_status_label.config(
                    text="⚠️ Not connected - start cursor control to see live status",
                    foreground="red"
                )
            else:
                self.connection_status_label.config(
                    text="⚠️ Waiting for state updates...",
                    foreground="orange"
                )

            # Reset all buttons to released
            for label in self.button_status_labels.values():
                label.config(text="Released", background="lightgray", foreground="black")

            self.mode_label.config(text="UNKNOWN", foreground="gray")
            self.last_action_label.config(text="No data")

        # Schedule next poll (100ms = 10Hz)
        self.root.after(100, self.poll_button_state)

    def apply_button_settings(self):
        """Apply button settings to configuration."""
        # Reverse action map
        action_map = {
            "Mouse Click": "mouse_click",
            "Keyboard": "keyboard",
            "None": "none"
        }

        # Update config for each button
        for button_name in self.button_action_vars.keys():
            action_display = self.button_action_vars[button_name].get()
            action = action_map.get(action_display, "none")
            value = self.button_value_vars[button_name].get()

            # Convert empty string to None
            if value == "":
                value = None

            self.config["buttons"][button_name] = {
                "action": action,
                "value": value
            }

        # Validate config
        if not config_manager.validate_config(self.config):
            messagebox.showerror("Error", "Invalid configuration values!")
            return

        # Save config
        if config_manager.save_config(self.runtime_config_path, self.config):
            messagebox.showinfo("Success", "Button settings applied successfully!")

            # Restart cursor control if it's running
            if self.cursor_process is not None:
                if messagebox.askyesno("Restart Required",
                                      "Cursor control needs to be restarted for changes to take effect. Restart now?"):
                    self.restart_cursor_control()
        else:
            messagebox.showerror("Error", "Failed to save configuration!")

    def save_profile(self):
        """Save current button configuration as a profile."""
        profile_name = self.profile_name_var.get().strip()
        if not profile_name:
            messagebox.showwarning("Warning", "Please enter a profile name!")
            return

        # Create profile config with only button settings
        profile_config = {"buttons": self.config["buttons"].copy()}

        # Save to profiles directory
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        if config_manager.save_config(profile_path, profile_config):
            messagebox.showinfo("Success", f"Profile '{profile_name}' saved successfully!")
            self.refresh_profile_list()
        else:
            messagebox.showerror("Error", "Failed to save profile!")

    def load_profile(self):
        """Load a button configuration profile."""
        profile_name = self.profile_list_var.get()
        if not profile_name:
            messagebox.showwarning("Warning", "Please select a profile to load!")
            return

        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        profile_config = config_manager.load_config(profile_path)

        if profile_config and "buttons" in profile_config:
            # Update config
            self.config["buttons"] = profile_config["buttons"]

            # Update UI
            action_map = {
                "mouse_click": "Mouse Click",
                "keyboard": "Keyboard",
                "none": "None"
            }

            for button_name in self.button_action_vars.keys():
                btn_config = self.config["buttons"].get(button_name, {"action": "none", "value": None})
                self.button_action_vars[button_name].set(action_map.get(btn_config["action"], "None"))
                self.button_value_vars[button_name].set(btn_config["value"] or "")

            messagebox.showinfo("Success", f"Profile '{profile_name}' loaded successfully!")
        else:
            messagebox.showerror("Error", "Failed to load profile!")

    def refresh_profile_list(self):
        """Refresh the list of available profiles."""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir, exist_ok=True)
            self.profile_combo['values'] = []
            return

        profiles = [f[:-5] for f in os.listdir(self.profiles_dir) if f.endswith('.json')]
        self.profile_combo['values'] = profiles

    def launch_cursor_control(self):
        """Launch the cursor control subprocess."""
        if self.cursor_process is not None:
            messagebox.showwarning("Warning", "Cursor control is already running!")
            return

        try:
            # Save current config before launching
            config_manager.save_config(self.runtime_config_path, self.config)

            # Launch subprocess
            self.cursor_process = subprocess.Popen(
                [self.python_path, self.cursor_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch cursor control: {e}")
            return False

    def stop_cursor_control(self):
        """Stop the cursor control subprocess."""
        if self.cursor_process is None:
            return

        try:
            self.cursor_process.terminate()
            self.cursor_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.cursor_process.kill()
            self.cursor_process.wait()
        finally:
            self.cursor_process = None

    def restart_cursor_control(self):
        """Restart the cursor control subprocess."""
        self.stop_cursor_control()
        return self.launch_cursor_control()

    def on_closing(self):
        """Handle window close event."""
        # Stop cursor control if running
        self.stop_cursor_control()
        # Close window
        self.root.destroy()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = JoyConGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
