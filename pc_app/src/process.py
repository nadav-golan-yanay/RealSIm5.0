from src.usb_to_rc_converter import USBToRCConverter

class Process:
    def __init__(self):
        """
        Initializes the Process class.
        """
        self.rc_converter = USBToRCConverter()  # Initialize the RC converter
        self.rc_channels = [1500] * 8  # Initialize RC channels with neutral PWM values
        self.ui_inputs = [0] * 8  # Placeholder for inputs from the UI
        self.current_process = "default_process"  # Add process selection

    def set_process(self, process_name):
        """
        Sets the current process type
        """
        self.current_process = process_name

    def update_ui_inputs(self, inputs):
        """
        Updates the inputs from the UI.
        """
        if len(inputs) == len(self.ui_inputs):
            self.ui_inputs = inputs
        else:
            raise ValueError("Mismatch in number of UI inputs. Expected 8 inputs.")

    def process_inputs(self):
        """
        Processes inputs from the UI and computes RC channel values.
        """
        self.apply_mixing_logic()
        self.update_rc_converter()

    def apply_mixing_logic(self):
        """
        Maps UI inputs to RC channel values and applies additional processing logic.
        """
        # Normalize inputs over 1000
        for i in range(len(self.rc_channels)):
            if self.ui_inputs[i] > 1000:
                self.ui_inputs[i] = self.ui_inputs[i] / 1000 - 1000
        
        # Apply selected process
        if self.current_process == "keyboard_process":
            # Channel 1 control (increment/decrement)
            if self.ui_inputs[0] == 1:
                self.rc_channels[0] += 100
            if self.ui_inputs[1] == 1:
                self.rc_channels[0] -= 100
            
            # Channel 2 control (increment/decrement)
            if self.ui_inputs[2] == 1:
                self.rc_channels[1] += 100
            if self.ui_inputs[3] == 1:
                self.rc_channels[1] -= 100
                
            # Direct mapping for remaining channels
            self.rc_channels[2] = (self.ui_inputs[4] * 1000 + 1000)
            self.rc_channels[3] = (self.ui_inputs[5] * 1000 + 1000)
            self.rc_channels[4] = (self.ui_inputs[6] * 1000 + 1000)
            self.rc_channels[5] = (self.ui_inputs[7] * 1000 + 1000)
            self.rc_channels[6] = 1500
            self.rc_channels[7] = 1500
            
        elif self.current_process == "custom_process":
            # Custom processing logic
            for i in range(len(self.rc_channels)):
                self.rc_channels[i] = (self.ui_inputs[i] * 1000 + 1000)
                
        else:  # default_process
            # Direct mapping for all channels
            for i in range(len(self.rc_channels)):
                self.rc_channels[i] = (self.ui_inputs[i] * 1000 + 1000)

        # Ensure RC channel values are within valid bounds
        for i in range(len(self.rc_channels)):
            if self.rc_channels[i] > 2000:
                self.rc_channels[i] = 2000
            if self.rc_channels[i] < 1000:
                self.rc_channels[i] = 1000

    def update_rc_converter(self):
        """
        Updates the RC converter with the computed RC channel values.
        """
        self.rc_converter.update_channels(self.rc_channels)

    def get_rc_channels(self):
        """
        Returns the computed RC channel values.
        """
        return self.rc_converter.get_channels()

    def get_rc_channels_display(self):
        """
        Returns a string representation of the RC channel values.
        """
        return self.rc_converter.get_channels_display()