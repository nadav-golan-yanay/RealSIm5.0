import os
import importlib
import tkinter as tk
import pygame  # Import pygame module
from tkinter import ttk, Frame
from src.usbController import list_available_devices
from src.usb_to_rc_converter import USBToRCConverter
from src import process  # Import the process module
from usb_comm import USBComm  # Ensure USBComm is imported

class AnyRC:
    def __init__(self, root):
        self.root = root
        self.root.title("AnyRC Controller")
        
        # Set application icon with correct path
        icon_path = r"C:\Users\nadav\OneDrive\Desktop\RealSIm5.0\pc_app\Icon\AnyRC_Icon.png"
        try:
            icon = tk.PhotoImage(file=icon_path, format="png")
            self.root.iconphoto(False, icon)
            self._icon = icon  # Keep a reference to prevent garbage collection
        except Exception as e:
            print(f"Failed to load icon from {icon_path}: {e}")
        
        # Create a frame for USB status and search button
        self.usb_frame = ttk.Frame(self.root)
        self.usb_frame.pack(fill='x', pady=5)
        
        # Add USB status label
        self.usb_status_label = ttk.Label(self.usb_frame, text="USB Status: Disconnected", font=("Arial", 10))
        self.usb_status_label.pack(side='left', padx=5)
        
        # Add Search USB button
        self.search_usb_button = ttk.Button(self.usb_frame, text="Search USB", command=self.search_usb)
        self.search_usb_button.pack(side='right', padx=5)
        
        self.usb_comm = None
        self.setup_usb_comm()  # Setup USB communication immediately

        self.rc_converter = USBToRCConverter()  # Initialize the RC converter
        self.process_module = process  # Store the process module
        self.process = process.Process()  # Initialize the Process class

        processor_file = r"C:\Users\nadav\OneDrive\Desktop\RealSIm5.0\pc_app\src\process.py"
        self.processor_file = processor_file  # Store the processor file path
        self.processor_last_modified = os.path.getmtime(self.processor_file)  # Track last modified time

        self.main_frame = Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        self.table_frame = ttk.Frame(self.main_frame)
        self.table_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Add table headers
        headers = ["Device", "Assign Input", "Assigned Input", "Input"]
        for col, header in enumerate(headers):
            label = ttk.Label(self.table_frame, text=header, font=("Arial", 10, "bold"))
            label.grid(row=0, column=col, padx=5, pady=5)

        self.rows = []
        for i in range(20):  # 20 rows for global variables
            row = {}

            # Device dropdown menu
            available_devices = list_available_devices()  # Get all available devices
            row["device"] = ttk.Combobox(self.table_frame, values=available_devices, state="readonly", width=20)
            row["device"].set("Keyboard")  # Default to Keyboard
            row["device"].grid(row=i + 1, column=0, padx=5, pady=5)

            # Assign input button
            row["assign_button"] = ttk.Button(self.table_frame, text="Assign Input", 
                                              command=lambda r=row: self.assign_input(r))
            row["assign_button"].grid(row=i + 1, column=1, padx=5, pady=5)

            # Assigned input display
            row["assigned_input"] = ttk.Entry(self.table_frame, state="readonly", width=15)
            row["assigned_input"].grid(row=i + 1, column=2, padx=5, pady=5)

            # Input display
            row["input_display"] = ttk.Entry(self.table_frame, state="readonly", width=15)
            row["input_display"].grid(row=i + 1, column=3, padx=5, pady=5)

            self.rows.append(row)

        # RC Channels Window
        self.rc_window = ttk.LabelFrame(self.main_frame, text="RC Channels")
        self.rc_window.pack(side="right", fill="y", padx=10, pady=10)

        self.rc_display = tk.Text(self.rc_window, height=30, width=50, state="disabled")  # Increased size
        self.rc_display.pack(padx=10, pady=10)

        # Add global Start/Stop Read buttons
        self.start_read_button = ttk.Button(self.main_frame, text="Start Read", command=self.start_read)
        self.start_read_button.pack(side="left", padx=10, pady=10)

        self.stop_read_button = ttk.Button(self.main_frame, text="Stop Read", command=self.stop_read)
        self.stop_read_button.pack(side="left", padx=10, pady=10)

        self.close_button = ttk.Button(self.main_frame, text="Close", command=self.close_app)
        self.close_button.pack(pady=10)

        # Add a button to open the processor file
        self.edit_processor_button = ttk.Button(self.main_frame, text="Edit Processor File", command=self.open_processor_file)
        self.edit_processor_button.pack(pady=10)

        self.current_row = None  # Track the row for which input is being assigned
        self.reading_inputs = False  # Track whether input reading is active
        self.update_rc_display_periodically()  # Now safe to call this

    def set_usb_comm(self, usb_comm):
        """
        Sets the USBComm instance for sending RC channels.
        """
        self.usb_comm = usb_comm

    def setup_usb_comm(self):
        """
        Detects and connects to the Arduino.
        """
        arduino_port = USBComm.detect_arduino()
        if arduino_port:
            self.usb_comm = USBComm(port=arduino_port)
            self.usb_comm.connect()

    def search_usb(self):
        """
        Searches for USB devices and attempts to reconnect.
        """
        if self.usb_comm:
            self.usb_comm.disconnect()
        
        self.setup_usb_comm()
        self.update_usb_status()

    def open_processor_file(self):
        """
        Opens the processor file in the default text editor.
        """
        try:
            os.system(f"notepad {self.processor_file}")  # Open the processor file in Notepad
        except Exception:
            pass

    def update_rc_display(self):
        """
        Updates the RC channel display in the UI.
        """
        # Fetch the latest RC channel values from the Process class
        channels_display = self.process.get_rc_channels_display()  # Get RC channel display as a string
        self.rc_display.config(state="normal")
        self.rc_display.delete("1.0", "end")  # Clear the RC display
        self.rc_display.insert("end", channels_display)  # Insert the updated RC channel values
        self.rc_display.config(state="disabled")  # Make the RC display read-only

        # Send RC channels to the Arduino if USBComm is set
        if self.usb_comm:
            self.usb_comm.send_rc_channels(self.process.get_rc_channels())

    def update_usb_status(self):
        """
        Updates the USB connection status label.
        """
        if self.usb_comm and self.usb_comm.serial_connection and self.usb_comm.serial_connection.is_open:
            self.usb_status_label.config(text="USB Status: Connected", foreground="green")
        else:
            self.usb_status_label.config(text="USB Status: Disconnected", foreground="red")
        self.root.after(1000, self.update_usb_status)  # Check every second

    def update_rc_display_periodically(self):
        """
        Periodically updates the RC channel display and USB status.
        """
        self.update_rc_display()
        self.update_usb_status()  # Start USB status updates
        self.root.after(100, self.update_rc_display_periodically)

    def close_app(self):
        """
        Closes the application and disconnects the Arduino.
        """
        if self.usb_comm:
            self.usb_comm.disconnect()
        self.root.destroy()

    def assign_input(self, row):
        """
        Assigns an input to the selected device.
        """
        selected_device = row["device"].get()
        if not selected_device:
            return

        if selected_device == "Keyboard":
            self.current_row = row
            self.root.bind("<KeyPress>", self.capture_key)  # Bind key press event
        else:
            # Simulate input assignment for non-keyboard devices
            assigned_input = "Input1"  # Placeholder for detected input
            row["assigned_input"].config(state="normal")
            row["assigned_input"].delete(0, "end")
            row["assigned_input"].insert(0, assigned_input)
            row["assigned_input"].config(state="readonly")

    def capture_key(self, event):
        """
        Captures the key pressed and assigns it to the current row.
        """
        if self.current_row:
            assigned_input = event.keysym  # Get the key symbol (e.g., "a", "Shift")
            self.current_row["assigned_input"].config(state="normal")
            self.current_row["assigned_input"].delete(0, "end")
            self.current_row["assigned_input"].insert(0, assigned_input)
            self.current_row["assigned_input"].config(state="readonly")
            self.root.unbind("<KeyPress>")  # Unbind the key press event
            self.current_row = None

    def start_read(self):
        """
        Starts reading input for all devices.
        """
        if self.reading_inputs:
            return

        self.reading_inputs = True
        self.root.bind("<KeyPress>", self.read_keyboard_input)  # Bind key press events
        self.root.bind("<KeyRelease>", self.read_keyboard_release)  # Bind key release events
        self.update_process_inputs()  # Start sending inputs to the process

    def stop_read(self):
        """
        Stops reading input for all devices.
        """
        if not self.reading_inputs:
            return

        self.reading_inputs = False
        self.root.unbind("<KeyPress>")  # Unbind key press events
        self.root.unbind("<KeyRelease>")  # Unbind key release events

    def reload_process_module(self):
        """
        Reloads the process module if it has been modified.
        """
        try:
            current_modified = os.path.getmtime(self.processor_file)
            if current_modified != self.processor_last_modified:
                self.processor_last_modified = current_modified
                importlib.reload(self.process_module)  # Reload the process module
                self.process = self.process_module.Process()  # Reinitialize the Process class
        except Exception:
            pass

    def update_process_inputs(self):
        """
        Periodically sends exactly 8 inputs from the UI to the Process class for processing.
        """
        if not self.reading_inputs:
            return

        # Reload the process module if it has been modified
        self.reload_process_module()

        # Collect inputs from the first 8 rows
        inputs = []
        for row in self.rows[:8]:  # Ensure only the first 8 rows are considered
            input_value = row["input_display"].get()
            inputs.append(int(input_value) if input_value.isdigit() else 0)

        # Pad with zeros if fewer than 8 rows are available
        while len(inputs) < 8:
            inputs.append(0)

        # Update the Process class with the inputs
        self.process.update_ui_inputs(inputs)
        self.process.process_inputs()

        # Schedule the next update
        self.root.after(100, self.update_process_inputs)  # Update every 100ms

    def read_keyboard_input(self, event):
        """
        Reads input from the keyboard and updates the corresponding input display when a key is pressed.
        """
        key_pressed = event.keysym  # Get the key symbol (e.g., "a", "Shift")

        # Update the input display only for rows where the key has been assigned
        for row in self.rows:
            assigned_key = row["assigned_input"].get()
            if assigned_key == key_pressed:  # Check if the pressed key matches the assigned key
                row["input_display"].config(state="normal")
                row["input_display"].delete(0, "end")
                row["input_display"].insert(0, 1)  # Button pressed, value is 1
                row["input_display"].config(state="readonly")

    def read_keyboard_release(self, event):
        """
        Reads input from the keyboard and updates the corresponding input display when a key is released.
        """
        key_released = event.keysym  # Get the key symbol (e.g., "a", "Shift")

        # Update the input display only for rows where the key has been assigned
        for row in self.rows:
            assigned_key = row["assigned_input"].get()
            if assigned_key == key_released:  # Check if the released key matches the assigned key
                row["input_display"].config(state="normal")
                row["input_display"].delete(0, "end")
                row["input_display"].insert(0, 0)  # Button released, value is 0
                row["input_display"].config(state="readonly")

    def read_joystick_input(self):
        """
        Reads input from the joystick and updates the corresponding input display.
        """
        if not self.rc_converter.joystick:
            return

        self.rc_converter.joystick.init()
        pygame.event.pump()  # Process joystick events

        # Map joystick axis values to 1000-2000 range
        for row in self.rows:
            if row["device"].get() == self.rc_converter.joystick.get_name():
                axis_value = self.rc_converter.joystick.get_axis(0)  # Example: Read axis 0
                mapped_value = int(1000 + (axis_value + 1) * 500)  # Map -1 to 1 range to 1000-2000
                row["input_display"].config(state="normal")
                row["input_display"].delete(0, "end")
                row["input_display"].insert(0, mapped_value)
                row["input_display"].config(state="readonly")
