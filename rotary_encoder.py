from gpiozero import RotaryEncoder, Button
from signal import pause
import logging

class RotaryEncoderHandler:
    def __init__(self, clk_pin, dt_pin, sw_pin, callback):
        self.rotary = RotaryEncoder(clk_pin, dt_pin)
        self.button = Button(sw_pin)
        self.callback = callback
        self.count = 0

        self.rotary.when_rotated_clockwise = self.rotated_clockwise
        self.rotary.when_rotated_counter_clockwise = self.rotated_counter_clockwise
        self.button.when_pressed = self.button_pressed
        self.button.when_released = self.button_released

        logging.info("RotaryEncoderHandler initialized")

    def rotated_clockwise(self):
        self.count += 1
        self.callback("RIGHT")
        logging.info(f"Rotary Encoder rotated clockwise, count: {self.count}")

    def rotated_counter_clockwise(self):
        self.count -= 1
        self.callback("LEFT")
        logging.info(f"Rotary Encoder rotated counter-clockwise, count: {self.count}")

    def button_pressed(self):
        self.callback("BUTTON", True)
        logging.info("Rotary Encoder button pressed")

    def button_released(self):
        self.callback("BUTTON", False)
        logging.info("Rotary Encoder button released")

    def get_count(self):
        return self.count

# Example callback function for demonstration
def example_callback(event, lock_state=None):
    if event == "BUTTON":
        print(f"Rotary Encoder Button {'Pressed' if lock_state else 'Released'}")
    elif event == "RIGHT":
        print("Rotary Encoder Turned Clockwise")
    elif event == "LEFT":
        print("Rotary Encoder Turned Counter Clockwise")

def example_callback_2(event, lock_state=None):
    if event == "BUTTON":
        print(f"Second Rotary Encoder Button {'Pressed' if lock_state else 'Released'}")
    elif event == "RIGHT":
        print("Second Rotary Encoder Turned Clockwise")
    elif event == "LEFT":
        print("Second Rotary Encoder Turned Counter Clockwise")

# Example usage
if __name__ == "__main__":
    encoder = RotaryEncoderHandler(13, 6, 5, example_callback)
    encoder_2 = RotaryEncoderHandler(21, 20, 16, example_callback_2)
    print("Rotary Encoders ready. Press Ctrl+C to exit.")
    pause()  # Keep the script running
