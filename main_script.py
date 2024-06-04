import threading
import time
import RPi.GPIO as GPIO
import logging
from multiprocessing import Process, Manager, Event
from oled_display import update_display_oled1, update_display_oled2
from data_broker import data_broker
from stepper_motor_control import motor_control_thread  # Import motor control function
from rotary_encoder import RotaryEncoderHandler
from buffer_manager import BufferManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Limit switches setup
limit_switch_x_left = 17
limit_switch_x_right = 18
limit_switch_y_top = 27
limit_switch_y_bottom = 22

GPIO.setup(limit_switch_x_left, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(limit_switch_x_right, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(limit_switch_y_top, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(limit_switch_y_bottom, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Motor control setup
motor_pin_x_dir = 23
motor_pin_x_step = 24
motor_pin_y_dir = 27
motor_pin_y_step = 22

GPIO.setup(motor_pin_x_dir, GPIO.OUT)
GPIO.setup(motor_pin_x_step, GPIO.OUT)
GPIO.setup(motor_pin_y_dir, GPIO.OUT)
GPIO.setup(motor_pin_y_step, GPIO.OUT)

if __name__ == "__main__":
    manager = Manager()
    shared_data = manager.dict({
        'pot_x': 0,
        'pot_y': 0,
        'X_speed': 10000,  # Set initial speed for X motor
        'Y_speed': 10000,  # Set initial speed for Y motor
        'dir_x': (0, 0),
        'dir_y': (0, 0),
        'mode': 0,
        'last_limit_x': 'None',
        'last_limit_y': 'None',
        'steps_x': 0,
        'steps_y': 0,
        'total_steps_x': 0,
        'total_steps_y': 0,
        'calibrating_x': True,
        'calibrating_y': True,
        'mode2': 1,
        'MOVEMENT_BUFFER_LEFT': 100,  # Default values for buffers
        'MOVEMENT_BUFFER_RIGHT': 200,
        'MOVEMENT_BUFFER_TOP': 100,
        'MOVEMENT_BUFFER_BOTTOM': 100,
        'current_mode': 'none'
    })

    encoder_state = manager.dict({
        'pressed': False,
        'last_press_time': time.time(),
        'adjustment_mode': 'none'
    })

    buffer_manager = BufferManager(shared_data, encoder_state)

    # Initialize the rotary encoders with the shared data and encoder state
    encoder = RotaryEncoderHandler(13, 6, 5, buffer_manager.encoder_callback)
    encoder_2 = RotaryEncoderHandler(21, 20, 16, buffer_manager.encoder_callback_2)

    display_process1 = Process(target=update_display_oled1, args=(shared_data,))
    display_process2 = Process(target=update_display_oled2, args=(shared_data, encoder_state))
    data_broker_process = Process(target=data_broker, args=(shared_data,))
    calibration_event_x = Event()
    calibration_event_y = Event()
    all_done_event = Event()

    motor_control_x_process = Process(target=motor_control_thread, args=("X", shared_data, calibration_event_x, all_done_event))
    motor_control_y_process = Process(target=motor_control_thread, args=("Y", shared_data, calibration_event_y, all_done_event))

    display_process1.start()
    display_process2.start()
    data_broker_process.start()
    motor_control_x_process.start()
    motor_control_y_process.start()

    # Wait for both calibrations to complete
    calibration_event_x.wait()
    calibration_event_y.wait()

    # Set the all_done_event to signal motors to start bounce mode
    all_done_event.set()

    display_process1.join()
    display_process2.join()
    data_broker_process.join()
    motor_control_x_process.join()
    motor_control_y_process.join()
