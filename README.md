# Multiprocessing Motor Control and Buffer Management System

This project is a multiprocessing system designed to control stepper motors in real-time with precision, ensuring they stay within defined buffer limits. It includes calibration, motor control, and real-time adjustments via rotary encoders, with feedback displayed on OLED screens.

## Features

- **Motor Control**: Precise control of X and Y stepper motors.
- **Calibration**: Automatic calibration of motor positions using limit switches.
- **Buffer Management**: Ensure motors stay within defined buffer limits.
- **Rotary Encoders**: Real-time adjustments of motor buffers and positions.
- **OLED Displays**: Display motor status, speeds, and buffer adjustments.
- **Logging**: Comprehensive logging for debugging and monitoring.

## Hardware Requirements

- Raspberry Pi (tested on Raspberry Pi 4 B)
- Stepper motors and drivers (e.g., TMC2208)
- Limit switches (Hall Effect Sensors used)
- Rotary encoders
- OLED displays


## Software Requirements

- Python 3.x
- `RPi.GPIO` library for GPIO control
- `logging` library for logging events and debugging
- `multiprocessing` library for parallel processing

## Pin Connections

### Motor Pins
- **X Motor**: 
  - Dir: GPIO 23
  - Step: GPIO 24
- **Y Motor**:
  - Dir: GPIO 27
  - Step: GPIO 22

### Limit Switch Pins
- **X Motor**:
  - Left: GPIO 10
  - Right: GPIO 9
- **Y Motor**:
  - Top: GPIO 11
  - Bottom: GPIO 0

### Rotary Encoder Pins
- **Encoder 1**:
  - CLK: GPIO 13
  - DT: GPIO 6
  - SW: GPIO 5
- **Encoder 2**:
  - CLK: GPIO 21
  - DT: GPIO 20
  - SW: GPIO 16

### OLED Pins
- **OLED 1**:
  - SCL: GPIO 1
  - SDA: GPIO 0
- **OLED 2**:
  - SCL: GPIO 1
  - SDA: GPIO 0

## Code Overview

### `main.py`

The entry point of the application. Initializes shared data, sets up GPIO, and starts multiprocessing threads for motor control, buffer management, and OLED display updates.

### `motor_control_thread.py`

Contains the logic for controlling the stepper motors, including calibration and movement within defined buffers. Handles acceleration and deceleration based on motor positions.

### `buffer_manager.py`

Manages the buffer limits and allows real-time adjustments using rotary encoders. Updates shared data with the latest buffer values.

### `oled_display.py`

Updates the OLED displays with current motor statuses, speeds, and buffer settings.

### `data_broker.py`

Handles data communication between different processes, ensuring synchronized updates and consistent states.

### `rotary_encoder.py`

Captures rotary encoder inputs and translates them into actions for adjusting motor positions and buffer limits.

## Future Improvements

## 1. Implementation of Acceleration Curves
- Adjust the smoothness of the motor functions within the buffer limits by implementing acceleration curves. This will provide smoother starts and stops for the motors, enhancing the overall performance and reducing mechanical stress.

## 2. Various Modes for Predefined Patterns
- Introduce various modes that allow the motors to move in predefined patterns. This will enable the system to create more organic tool paths, moving beyond the current linear motion to incorporate curved and complex movements.

## 3. More Dynamic Motor Speed Adjustments
- Implement more dynamic motor speed adjustments. This could include features such as automatic speed changes based on the load or specific tasks, allowing for more efficient and precise operations.

## 4. Enhanced Menu System
- Develop a more robust menu system for the operating system, navigable via rotary encoders. This enhanced menu system will allow users to easily select and adjust different settings and modes, providing a more user-friendly interface.

## 5. Additional Menu System Features
- Add new features to the menu system to enable easier navigation and control over the system's functionalities. This could include graphical representations, detailed settings adjustments, and quick access to frequently used features.


## License
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International Public License**
