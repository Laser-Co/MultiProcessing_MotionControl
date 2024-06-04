import serial
import time
import logging

def data_broker(shared_data):
    logging.info("Starting data broker...")
    try:
        serial_port = '/dev/ttyACM0'
        baud_rate = 115200

        ser = serial.Serial(serial_port, baud_rate)
        logging.info(f"Serial port {serial_port} opened successfully")

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                logging.info(f"Serial data received: {line}")

                if line:
                    values = list(map(int, line.split(' ')))
                    shared_data.update({
                        'pot_x': values[0],
                        'pot_y': values[1],
                        'switch_x': (values[2], values[3]),  # Adding switch state
                        'switch_y': (values[6], values[7]),  # Adding switch state
                        'mode': values[4],
                        'mode2': values[5]
                    })
                    logging.info(f"Updated shared_data: {shared_data}")

            time.sleep(0.05)  # Adjust to ensure faster updates

    except serial.SerialException as e:
        logging.error(f"Error opening serial port {serial_port}: {e}")
    except Exception as e:
        logging.error(f"Error in data_broker: {e}")
    finally:
        if ser.is_open:
            ser.close()
        logging.info("Exiting data broker.")
