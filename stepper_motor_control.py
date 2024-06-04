import threading
import time
import RPi.GPIO as GPIO
import logging
from multiprocessing import Process, Manager, Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Suppress GPIO warnings
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

motor_pins = {
    "X_Dir": 23,
    "X_Step": 24,
    "Y_Dir": 27,
    "Y_Step": 22,
}

limit_switch_pins = {
    "X_Left": 10, "X_Right": 9,
    "Y_Top": 11, "Y_Bottom": 0
}

direction_descriptions = {
    "X": {(1, 0): "Right", (0, 1): "Left"},
    "Y": {(1, 0): "Up", (0, 1): "Down"}
}

for pin in motor_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
for pin in limit_switch_pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def map_value(value, from_low, from_high, to_low, to_high):
    return to_low + (to_high - to_low) * (value - from_low) / (from_high - from_low)

def sleep(time_value, unit='us'):
    if unit == 'us':
        seconds = time_value / 1_000_000.0
    elif unit == 'ms':
        seconds = time_value / 1_000.0
    else:
        raise ValueError("Invalid unit. Use 'us' for microseconds or 'ms'.")
    time.sleep(seconds)

def stop_motor(step_pin):
    GPIO.output(step_pin, GPIO.LOW)

def move_motor(dir_pin, step_pin, direction, speed):
    GPIO.output(dir_pin, GPIO.HIGH if direction[0] else GPIO.LOW)
    GPIO.output(step_pin, GPIO.HIGH)
    sleep(speed, 'us')
    GPIO.output(step_pin, GPIO.LOW)
    sleep(speed, 'us')

def check_and_correct_position(motor, shared_data):
    steps = shared_data[f'steps_{motor.lower()}']
    total_steps = shared_data[f'total_steps_{motor.lower()}']
    if motor == "X":
        movement_buffer_left = shared_data.get('MOVEMENT_BUFFER_LEFT', 100)
        movement_buffer_right = shared_data.get('MOVEMENT_BUFFER_RIGHT', 200)
        if steps < movement_buffer_left:
            steps = movement_buffer_left
            shared_data[f'steps_{motor.lower()}'] = steps
            logger.info(f"Adjusted {motor} steps to movement_buffer_left: {movement_buffer_left}")
        elif steps > total_steps - movement_buffer_right:
            steps = total_steps - movement_buffer_right
            shared_data[f'steps_{motor.lower()}'] = steps
            logger.info(f"Adjusted {motor} steps to movement_buffer_right: {total_steps - movement_buffer_right}")
    elif motor == "Y":
        movement_buffer_bottom = shared_data.get('MOVEMENT_BUFFER_BOTTOM', 100)
        movement_buffer_top = shared_data.get('MOVEMENT_BUFFER_TOP', 100)
        if steps < movement_buffer_bottom:
            steps = movement_buffer_bottom
            shared_data[f'steps_{motor.lower()}'] = steps
            logger.info(f"Adjusted {motor} steps to movement_buffer_bottom: {movement_buffer_bottom}")
        elif steps > total_steps - movement_buffer_top:
            steps = total_steps - movement_buffer_top
            shared_data[f'steps_{motor.lower()}'] = steps
            logger.info(f"Adjusted {motor} steps to movement_buffer_top: {total_steps - movement_buffer_top}")

def motor_control_thread(motor, shared_data, calibration_event, all_done_event):
    dir_pin = motor_pins[f"{motor}_Dir"]
    step_pin = motor_pins[f"{motor}_Step"]

    if motor == "X":
        limit_pos = limit_switch_pins["X_Right"]
        limit_neg = limit_switch_pins["X_Left"]
        calibration_speed = 1000  # Calibration speed for X motor
    elif motor == "Y":
        limit_pos = limit_switch_pins["Y_Top"]
        limit_neg = limit_switch_pins["Y_Bottom"]
        calibration_speed = 1500  # Calibration speed for Y motor

    def get_acceleration_speed(steps, total_steps, base_speed, max_speed):
        buffer_distance = shared_data.get('ACCELERATION_BUFFER', 20)  # Default to 20 if not set
        if steps < buffer_distance:
            # Accelerate
            speed = base_speed + ((max_speed - base_speed) * (steps / buffer_distance))
        elif steps > total_steps - buffer_distance:
            # Decelerate
            speed = base_speed + ((max_speed - base_speed) * ((total_steps - steps) / buffer_distance))
        else:
            # Maintain max speed
            speed = max_speed
        return int(speed)

    try:
        logger.info(f"Calibrating {motor} motor...")
        shared_data[f'calibrating_{motor.lower()}'] = True

        # Calibrate to negative limit switch
        while GPIO.input(limit_neg):
            move_motor(dir_pin, step_pin, (0, 1), calibration_speed)
            shared_data[f'dir_{motor.lower()}'] = (0, 1)

        shared_data[f'steps_{motor.lower()}'] = 0
        
        # Calibrate to positive limit switch and count steps
        while GPIO.input(limit_pos):
            move_motor(dir_pin, step_pin, (1, 0), calibration_speed)
            shared_data[f'dir_{motor.lower()}'] = (1, 0)
            shared_data[f'steps_{motor.lower()}'] += 1
        
        total_steps = shared_data[f'steps_{motor.lower()}']
        shared_data[f'total_steps_{motor.lower()}'] = total_steps

        # Move to the center position
        half_steps = total_steps // 2
        for _ in range(half_steps):
            move_motor(dir_pin, step_pin, (0, 1), calibration_speed)
            shared_data[f'dir_{motor.lower()}'] = (0, 1)
            shared_data[f'steps_{motor.lower()}'] -= 1
        
        logger.info(f"{motor} motor calibration complete. Total steps: {total_steps}")

        # Set canvas frame after calibration
        if motor == "X":
            shared_data['CANVAS_FRAME_X'] = total_steps
        elif motor == "Y":
            shared_data['CANVAS_FRAME_Y'] = total_steps

        shared_data[f'calibrating_{motor.lower()}'] = False
        calibration_event.set()
        all_done_event.wait()

        # Bounce mode using memory and buffer
        direction = (1, 0)
        initial_direction_set = False  # Flag to indicate if the initial direction has been set

        while True:
            switch_state = shared_data[f'switch_{motor.lower()}']
            if switch_state == (0, 0):  # Middle position, stop the motor
                stop_motor(step_pin)
                shared_data[f'{motor}_speed'] = 0
                shared_data[f'dir_{motor.lower()}'] = (0, 0)
                initial_direction_set = False  # Reset the flag if in the middle position
            else:
                if not initial_direction_set:
                    if switch_state == (0, 1):  # Move left/down
                        direction = (0, 1)
                    elif switch_state == (1, 0):  # Move right/up
                        direction = (1, 0)
                    initial_direction_set = True  # Set the flag to indicate the initial direction has been set

                pot_value = shared_data[f'pot_{motor.lower()}']
                base_speed = map_value(pot_value, 300, 65535, 500000, 250)  # Example base speed range
                max_speed = base_speed / 2  # Example max speed range
                steps = shared_data[f'steps_{motor.lower()}']
                total_steps = shared_data[f'total_steps_{motor.lower()}']

                check_and_correct_position(motor, shared_data)

                speed = get_acceleration_speed(steps, total_steps, base_speed, max_speed)
                shared_data[f'{motor}_speed'] = speed  # Update shared data with the current speed

                if direction == (1, 0) and steps >= total_steps - shared_data.get('MOVEMENT_BUFFER_RIGHT', 200):
                    logger.info(f"{motor} motor near positive limit. Reversing direction.")
                    direction = (0, 1)
                    shared_data[f'dir_{motor.lower()}'] = direction
                elif direction == (0, 1) and steps <= shared_data.get('MOVEMENT_BUFFER_LEFT', 100):
                    logger.info(f"{motor} motor near negative limit. Reversing direction.")
                    direction = (1, 0)
                    shared_data[f'dir_{motor.lower()}'] = direction

                move_motor(dir_pin, step_pin, direction, speed)

                if direction == (1, 0):
                    shared_data[f'steps_{motor.lower()}'] += 1
                else:
                    shared_data[f'steps_{motor.lower()}'] -= 1

                # Update the direction in the shared data
                shared_data[f'dir_{motor.lower()}'] = direction

                logger.info(f"{motor} motor direction after move: {direction}, steps after move: {shared_data[f'steps_{motor.lower()}']}")

            # Reduce sleep time to improve response time
            time.sleep(0.01)  # Adjust as necessary

    except KeyboardInterrupt:
        logger.info(f"Motor control thread for {motor} interrupted")
    except Exception as e:
        logger.error(f"Error in motor_control_thread for motor {motor}: {e}")

if __name__ == "__main__":
    manager = Manager()
    shared_data = manager.dict({
        'pot_x': 0,
        'pot_y': 0,
        'X_speed': 0,
        'Y_speed': 0,
        'dir_x': (0, 0),
        'dir_y': (0, 0),
        'mode': 0,
        'last_limit_x': 'None',
        'last_limit_y': 'None',
        'steps_x': 0,
        'steps_y': 0,
        'total_steps_x': 0,
        'total_steps_y': 0,
        'calibrating_x': False,
        'calibrating_y': False,
        'mode2': 0,
        'MOVEMENT_BUFFER_LEFT': 0,
        'MOVEMENT_BUFFER_RIGHT': 0,
        'MOVEMENT_BUFFER_TOP': 0,
        'MOVEMENT_BUFFER_BOTTOM': 160,
        'current_mode': 'y_scale',
        'switch_x': (0, 0),
        'switch_y': (0, 0),
        'CANVAS_FRAME_X': 0,
        'CANVAS_FRAME_Y': 0
    })

    calibration_event = Event()
    all_done_event = Event()

    x_motor_thread = threading.Thread(target=motor_control_thread, args=("X", shared_data, calibration_event, all_done_event))
    y_motor_thread = threading.Thread(target=motor_control_thread, args=("Y", shared_data, calibration_event, all_done_event))

    x_motor_thread.start()
    y_motor_thread.start()

    x_motor_thread.join()
    y_motor_thread.join()
