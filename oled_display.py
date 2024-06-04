from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont
import time
import logging
from multiprocessing import Process, Manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

# Initialization for both OLED displays
serial1 = i2c(port=1, address=0x3C)
oled1 = ssd1306(serial1)

serial2 = i2c(port=1, address=0x3D)
oled2 = ssd1306(serial2)

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(font_path, 12)
font_small = ImageFont.truetype(font_path, 10)
font_large = ImageFont.truetype(font_path, 25)
mode_area_width = 40

def map_pot_value(value, from_low, from_high, to_low, to_high):
    value = max(from_low, min(from_high, value))
    return to_low + (to_high - to_low) * (value - from_low) / (from_high - from_low)

def draw_bar(draw, x, y, width, height, fill="white"):
    draw.rectangle((x, y, x + width, y + height), outline="white", fill=fill)

def update_display_oled1(shared_data):
    try:
        while True:
            with canvas(oled1) as draw:
                mode_area_start = oled1.width - mode_area_width
                max_bar_width = oled1.width // 3

                up_arrow = "\u2191"
                down_arrow = "\u2193"
                left_arrow = "\u2190"
                right_arrow = "\u2192"
                no_direction = "~"

                x_speed = shared_data.get('X_speed', 0)
                y_speed = shared_data.get('Y_speed', 0)

                mid_y_position = oled1.height // 2
                draw.rectangle((mode_area_start, 0, oled1.width, oled1.height), fill="black")
                max_content_width = mode_area_start - 5
                for x in range(0, oled1.width, 4):
                    draw.point((x - 50, mid_y_position), fill="white")

                pot_raw_X = shared_data.get('pot_x', 0)
                pot_raw_Y = shared_data.get('pot_y', 0)
                dir_y = shared_data.get('dir_y', (0, 0))
                dir_x = shared_data.get('dir_x', (0, 0))
                mode = shared_data.get('mode', 1)

                mapped_pot_value_x = int(map_pot_value(pot_raw_X, 0, 65535, 500, 5000))  # Example speed range
                mapped_pot_value_y = int(map_pot_value(pot_raw_Y, 0, 65535, 500, 5000))  # Example speed range

                bar_width_x = int((mapped_pot_value_x / 5000.0) * max_bar_width)  # Adjust based on max speed
                bar_width_y = int((mapped_pot_value_y / 5000.0) * max_bar_width)  # Adjust based on max speed

                draw_bar(draw, 0, mid_y_position + 10, bar_width_x, 8, fill="white")
                draw.text((0, mid_y_position + 20), f"X:{x_speed}", fill="white", font=font)  # Display speed

                draw_bar(draw, 0, 0, bar_width_y, 8, fill="white")
                draw.text((0, mid_y_position - 20), f"Y: {y_speed}", fill="white", font=font)

                switch_indicator_x = no_direction
                if dir_x == (1, 0):
                    switch_indicator_x = right_arrow
                elif dir_x == (0, 1):
                    switch_indicator_x = left_arrow

                switch_indicator_y = no_direction
                if dir_y == (1, 0):
                    switch_indicator_y = up_arrow
                elif dir_y == (0, 1):
                    switch_indicator_y = down_arrow

                draw.text((max_bar_width + 16, mid_y_position + 20), f"X: {switch_indicator_x}", fill="white", font=font)
                draw.text((max_bar_width + 16, 15), f"Y: {switch_indicator_y}", fill="white", font=font)
                draw.text((mode_area_start + 5, 2), "MODE:", fill="white", font=font_small)
                draw.text((mode_area_start + 15, 12), f"{mode}", fill="white", font=font_large)

            time.sleep(0.05)
    except KeyboardInterrupt:
        logging.info("OLED1 display update interrupted")
    except Exception as e:
        logging.error(f"Error in update_display_oled1: {e}")

def update_display_oled2(shared_data, encoder_state):
    try:
        dot_count = 1  # Initialize dot count for the animation
        while True:
            # Logging to verify the received shared data
            logging.info(f"OLED2 - shared_data: {shared_data}")
            logging.info(f"OLED2 - steps_y: {shared_data.get('steps_y')}")
            logging.info(f"OLED2 - encoder_state: {encoder_state}")

            with canvas(oled2) as draw:
                calibrating_x = shared_data.get('calibrating_x', True)
                calibrating_y = shared_data.get('calibrating_y', True)

                if calibrating_x or calibrating_y:
                    # Create the animated "Calibrating" message
                    dots = '.' * dot_count
                    message = f"Calibrating{dots}"
                    draw.text((0, 0), message, fill="white", font=font)

                    if not calibrating_x:
                        draw.text((0, 20), "X motor done", fill="white", font=font)
                    if not calibrating_y:
                        draw.text((0, 40), "Y motor done", fill="white", font=font)

                    dot_count = (dot_count % 3) + 1  # Update dot count for animation

                else:
                    total_steps_x = shared_data.get('total_steps_x', 0)
                    total_steps_y = shared_data.get('total_steps_y', 0)
                    steps_x = shared_data.get('steps_x', 0)
                    steps_y = shared_data.get('steps_y', 0)

                    movement_buffer_left = shared_data.get('MOVEMENT_BUFFER_LEFT', 0)
                    movement_buffer_right = shared_data.get('MOVEMENT_BUFFER_RIGHT', 0)
                    movement_buffer_top = shared_data.get('MOVEMENT_BUFFER_TOP', 0)
                    movement_buffer_bottom = shared_data.get('MOVEMENT_BUFFER_BOTTOM', 0)

                    oled_width = oled2.width
                    oled_height = oled2.height

                    rect_left = 10
                    rect_top = 20
                    rect_right = oled_width - 10
                    rect_bottom = oled_height - 10

                    scale_x = (rect_right - rect_left) / total_steps_x
                    scale_y = (rect_bottom - rect_top) / total_steps_y

                    rect_right = rect_left + int(total_steps_x * scale_x)
                    rect_bottom = rect_top + int(total_steps_y * scale_y)

                    new_left = rect_left + int(movement_buffer_left * scale_x)
                    new_right = rect_right - int(movement_buffer_right * scale_x)
                    new_top = rect_top + int(movement_buffer_top * scale_y)
                    new_bottom = rect_bottom - int(movement_buffer_bottom * scale_y)

                    new_left = max(rect_left, min(new_left, rect_right))
                    new_right = max(rect_left, min(new_right, rect_right))
                    new_top = max(rect_top, min(new_top, rect_bottom))
                    new_bottom = max(rect_top, min(new_bottom, rect_bottom))

                    draw.rectangle((rect_left, rect_top, rect_right, rect_bottom), outline="white")

                    for y in range(rect_top, rect_bottom, 4):
                        draw.point((new_left, y), fill="white")
                        draw.point((new_right, y), fill="white")
                    for x in range(rect_left, rect_right, 4):
                        draw.point((x, new_top), fill="white")
                        draw.point((x, new_bottom), fill="white")

                    if total_steps_x > 0:
                        pos_x = rect_left + int((steps_x / total_steps_x) * (rect_right - rect_left))
                    else:
                        pos_x = rect_left

                    if total_steps_y > 0:
                        pos_y = rect_bottom - int((steps_y / total_steps_y) * (rect_bottom - rect_top))
                    else:
                        pos_y = rect_bottom

                    dot_radius = 2
                    draw.ellipse((pos_x - dot_radius, pos_y - dot_radius, pos_x + dot_radius, pos_y + dot_radius), fill="white")

                    draw.text((0, 0), f"X: {steps_x}/{total_steps_x}", fill="white", font=font_small)
                    draw.text((0, 10), f"Y: {steps_y}/{total_steps_y}", fill="white", font=font_small)

                    x_speed = shared_data.get('X_speed', 0)
                    y_speed = shared_data.get('Y_speed', 0)
                    dir_x = shared_data.get('dir_x', (0, 0))
                    dir_y = shared_data.get('dir_y', (0, 0))

                    future_steps_x = min(200, total_steps_x - steps_x) if dir_x == (1, 0) else max(-200, -steps_x)
                    future_steps_y = min(200, total_steps_y - steps_y) if dir_y == (1, 0) else max(-200, -steps_y)

                    future_pos_x = pos_x + int(future_steps_x * scale_x)
                    future_pos_y = pos_y - int(future_steps_y * scale_y)

                    future_pos_x = max(rect_left, min(future_pos_x, rect_right))
                    future_pos_y = max(rect_top, min(future_pos_y, rect_bottom))

                    if dir_x != (0, 0) or dir_y != (0, 0):
                        steps = max(abs(future_steps_x), abs(future_steps_y))
                        for step in range(0, steps, 4):
                            if dir_x != (0, 0):
                                trajectory_x = pos_x + int((step if dir_x == (1, 0) else -step) * scale_x)
                                trajectory_x = max(rect_left, min(trajectory_x, rect_right))
                            else:
                                trajectory_x = pos_x
                            if dir_y != (0, 0):
                                trajectory_y = pos_y - int((step if dir_y == (1, 0) else -step) * scale_y)
                                trajectory_y = max(rect_top, min(trajectory_y, rect_bottom))
                            else:
                                trajectory_y = pos_y
                            draw.point((trajectory_x, trajectory_y), fill="white")

                    mode_text = f"Mode: {shared_data.get('current_mode', 'none')}"
                    logging.info(f"Displaying Mode: {shared_data.get('current_mode', 'none')}")
                    draw.text((oled2.width - 80, 0), mode_text, fill="white", font=font_small)

            time.sleep(0.05)
    except KeyboardInterrupt:
        logging.info("OLED2 display update interrupted")
    except Exception as e:
        logging.error(f"Error in update_display_oled2: {e}")


if __name__ == "__main__":
    manager = Manager()
    shared_data = manager.dict({
        'total_steps_x': 733,
        'total_steps_y': 541,
        'steps_x': 367,
        'steps_y': 271,
        'X_speed': 0,
        'Y_speed': 0,
        'dir_x': (1, 0),
        'dir_y': (0, 0),
        'MOVEMENT_BUFFER_LEFT': 200,
        'MOVEMENT_BUFFER_RIGHT': 200,
        'MOVEMENT_BUFFER_TOP': 50,
        'MOVEMENT_BUFFER_BOTTOM': 50,
        'current_mode': 'none',  # Ensure this key is present
    })

    encoder_state = {
        'pressed': False,
        'last_press_time': time.time(),
        'adjustment_mode': 'none',
        'pressed_2': False,
        'last_press_time_2': time.time(),
        'adjustment_mode_2': 'none'
    }

    display_process1 = Process(target=update_display_oled1, args=(shared_data,))
    display_process2 = Process(target=update_display_oled2, args=(shared_data, encoder_state))
    display_process1.start()
    display_process2.start()
    display_process1.join()
    display_process2.join()
