import time
import logging


class BufferManager:
    def __init__(self, shared_data, encoder_state):
        self.shared_data = shared_data
        self.encoder_state = encoder_state
        self.encoder_state['adjustment_mode'] = 'none'
        self.encoder_state['last_press_time'] = time.time()
        self.encoder_state['pressed'] = False

        self.encoder_state['adjustment_mode_2'] = 'none'
        self.encoder_state['last_press_time_2'] = time.time()
        self.encoder_state['pressed_2'] = False

        # Define the list of menu states
        self.menu_states = ['none', 'x_scale', 'x_position', 'y_scale', 'y_position']
        self.current_state_index = 0

    def encoder_callback(self, event, lock_state=None):
        logging.info(f"Encoder event: {event}, lock_state: {lock_state}")
        if event == "BUTTON":
            self.handle_encoder_press(lock_state)
        elif event == "RIGHT":
            self.handle_encoder_rotation(1)
        elif event == "LEFT":
            self.handle_encoder_rotation(-1)

    def encoder_callback_2(self, event, lock_state=None):
        logging.info(f"Encoder 2 event: {event}, lock_state: {lock_state}")
        if event == "BUTTON":
            self.handle_encoder_press_2(lock_state)
        elif event == "RIGHT":
            self.handle_encoder_rotation_2(1)
        elif event == "LEFT":
            self.handle_encoder_rotation_2(-1)


    def handle_encoder_press(self, pressed):
            current_time = time.time()
            if current_time - self.encoder_state['last_press_time'] > 0.5:
                self.encoder_state['pressed'] = pressed
                self.encoder_state['last_press_time'] = current_time
                if pressed:
                    self.current_state_index = (self.current_state_index + 1) % len(self.menu_states)
                    self.encoder_state['adjustment_mode'] = self.menu_states[self.current_state_index]
                    self.shared_data['current_mode'] = self.encoder_state['adjustment_mode']
                    logging.info(f"Encoder pressed. Mode: {self.encoder_state['adjustment_mode']}")

    def handle_encoder_rotation(self, rotation_value):
        if self.encoder_state['adjustment_mode'] == 'x_scale':
            self.adjust_x_scale(rotation_value)
        elif self.encoder_state['adjustment_mode'] == 'y_scale':
            self.adjust_y_scale(rotation_value)
        elif self.encoder_state['adjustment_mode'] == 'x_position':
            self.adjust_x_position(rotation_value)
        elif self.encoder_state['adjustment_mode'] == 'y_position':
            self.adjust_y_position(rotation_value)

    def adjust_x_position(self, rotation_value):
        delta = rotation_value * 20
        delta = -delta
        new_left_value = self.shared_data['MOVEMENT_BUFFER_LEFT'] - delta
        self.shared_data['MOVEMENT_BUFFER_LEFT'] = max(0, new_left_value)
        new_right_value = self.shared_data['MOVEMENT_BUFFER_RIGHT'] + delta
        self.shared_data['MOVEMENT_BUFFER_RIGHT'] = min(self.shared_data['total_steps_x'], new_right_value)
        logging.info(f"Adjusted X scale: LEFT = {self.shared_data['MOVEMENT_BUFFER_LEFT']}, RIGHT = {self.shared_data['MOVEMENT_BUFFER_RIGHT']}")

    def adjust_y_position(self, rotation_value):
        delta = rotation_value * 20
        delta = -delta
        new_bottom_value = self.shared_data['MOVEMENT_BUFFER_BOTTOM'] - delta
        self.shared_data['MOVEMENT_BUFFER_BOTTOM'] = max(0, new_bottom_value)
        new_top_value = self.shared_data['MOVEMENT_BUFFER_TOP'] + delta
        self.shared_data['MOVEMENT_BUFFER_TOP'] = min(self.shared_data['total_steps_y'], new_top_value)
        logging.info(f"Adjusted Y scale: BOTTOM = {self.shared_data['MOVEMENT_BUFFER_BOTTOM']}, TOP = {self.shared_data['MOVEMENT_BUFFER_TOP']}")

    def adjust_x_scale(self, rotation_value):
        delta = rotation_value * 10  # Adjust the multiplier as needed
        delta = -delta
        new_left_value = self.shared_data['MOVEMENT_BUFFER_LEFT'] + delta
        new_right_value = self.shared_data['MOVEMENT_BUFFER_RIGHT'] + delta
        self.shared_data['MOVEMENT_BUFFER_LEFT'] = max(0, min(new_left_value, self.shared_data['total_steps_x']))
        self.shared_data['MOVEMENT_BUFFER_RIGHT'] = max(0, min(new_right_value, self.shared_data['total_steps_x']))
        logging.info(f"Adjusted X position: LEFT = {self.shared_data['MOVEMENT_BUFFER_LEFT']}, RIGHT = {self.shared_data['MOVEMENT_BUFFER_RIGHT']}")

    def adjust_y_scale(self, rotation_value):
        delta = rotation_value * 10  # Adjust the multiplier as needed
        delta = -delta
        new_top_value = self.shared_data['MOVEMENT_BUFFER_TOP'] + delta
        new_bottom_value = self.shared_data['MOVEMENT_BUFFER_BOTTOM'] + delta
        self.shared_data['MOVEMENT_BUFFER_TOP'] = max(0, min(new_top_value, self.shared_data['total_steps_y']))
        self.shared_data['MOVEMENT_BUFFER_BOTTOM'] = max(0, min(new_bottom_value, self.shared_data['total_steps_y']))
        logging.info(f"Adjusted Y position: TOP = {self.shared_data['MOVEMENT_BUFFER_TOP']}, BOTTOM = {self.shared_data['MOVEMENT_BUFFER_BOTTOM']}")

def update_shared_data_with_buffers(shared_data):
    shared_data['MOVEMENT_BUFFER_LEFT'] = 100  # Define left movement limit
    shared_data['MOVEMENT_BUFFER_RIGHT'] = 200  # Define right movement limit
    shared_data['MOVEMENT_BUFFER_TOP'] = 100  # Define top movement limit
    shared_data['MOVEMENT_BUFFER_BOTTOM'] = 100  # Define bottom movement limit
    shared_data['ACCELERATION_BUFFER'] = 20  # Define acceleration buffer region size

def buffer_update_process(shared_data):
    while True:
        update_shared_data_with_buffers(shared_data)
        time.sleep(1)  # Update the buffers at regular intervals, adjust as necessary

if __name__ == "__main__":
    from multiprocessing import Manager, Process
    manager = Manager()
    shared_data = manager.dict({
        'steps_x': 0,
        'steps_y': 0,
        'total_steps_x': 1000,
        'total_steps_y': 1000,
        'MOVEMENT_BUFFER_LEFT': 0,
        'MOVEMENT_BUFFER_RIGHT': 1000,
        'MOVEMENT_BUFFER_TOP': 1000,
        'MOVEMENT_BUFFER_BOTTOM': 0,
        'current_mode': 'none',
    })
    encoder_state = manager.dict({
        'adjustment_mode': 'none',
        'last_press_time': time.time(),
        'pressed': False
    })

    # Initialize shared data with buffers
    update_shared_data_with_buffers(shared_data)

    buffer_manager = BufferManager(shared_data, encoder_state)

    # Start the buffer update process
    buffer_process = Process(target=buffer_update_process, args=(shared_data,))
    buffer_process.start()

    # Simulate encoder events for testing purposes
    while True:
        # Simulate an encoder press event
        buffer_manager.encoder_callback("BUTTON", True)
        time.sleep(2)
        # Simulate an encoder rotation to the right
        buffer_manager.encoder_callback("RIGHT")
        time.sleep(1)
        # Simulate an encoder rotation to the left
        buffer_manager.encoder_callback("LEFT")
        time.sleep(1)
        # Simulate another encoder press event
        buffer_manager.encoder_callback("BUTTON", True)
        time.sleep(2)