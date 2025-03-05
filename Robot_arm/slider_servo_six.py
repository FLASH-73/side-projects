#!/usr/bin/env python
#
# *********     GUI Multi-Servo Control Example      *********
#
# Controls five STServo servos (IDs 2-6) with individual sliders (0-12288) and displays their current positions and speeds
# Tested with STServo and FE-URT-1 on macOS
#

import sys
import os
import tkinter as tk
from threading import Thread
import time

if os.name == 'nt':
    import msvcrt
else:
    import tty, termios

# Adjust path if STservo_sdk is in the same directory
sys.path.append("..")
from STservo_sdk import *  # Uses STServo SDK library

# Default settings
BAUDRATE = 1000000         # STServo default baudrate: 1 Mbps
DEVICENAME = '/dev/cu.usbserial-2140'  # Your Mac port
STS_MINIMUM_POSITION_VALUE = 0
STS_MAXIMUM_POSITION_VALUE = 12288  # Multi-turn range (adjustable up to ±28672)
STS_MOVING_SPEED = 1500    # Moving speed
STS_MOVING_ACC = 50        # Moving acceleration
STS_MODE_ADDR = 33         # Mode register address
STS_TORQUE_ENABLE_ADDR = 40  # Torque enable address
STS_MIN_ANGLE_LIMIT_ADDR = 9  # Min angle limit address
STS_MAX_ANGLE_LIMIT_ADDR = 11  # Max angle limit address
STS_LOCK_ADDR = 55         # Lock register address

# Initialize PortHandler and PacketHandler
portHandler = PortHandler(DEVICENAME)
packetHandler = sts(portHandler)

# Open port
if not portHandler.openPort():
    print("Failed to open the port")
    sys.exit(1)
print("Succeeded to open the port")

# Set baudrate
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to change the baudrate")
    portHandler.closePort()
    sys.exit(1)
print("Succeeded to change the baudrate")

# Initialize servos: set mode to 0, enable multi-turn, and read initial positions
initial_positions = [0] * 5  # For servos 2 to 6
for i in range(5):  # i from 0 to 4, corresponding to servos 2 to 6
    servo_id = i + 2
    # Disable torque
    sts_comm_result, sts_error = packetHandler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE_ADDR, 0)
    if sts_comm_result != COMM_SUCCESS:
        print(f"Failed to disable torque for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
        continue
    # Unlock EEPROM
    sts_comm_result, sts_error = packetHandler.write1ByteTxRx(servo_id, STS_LOCK_ADDR, 0)
    if sts_comm_result != COMM_SUCCESS:
        print(f"Failed to unlock EEPROM for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
        continue
    # Set mode to 0 (position servo mode)
    sts_comm_result, sts_error = packetHandler.write1ByteTxRx(servo_id, STS_MODE_ADDR, 0)
    if sts_comm_result != COMM_SUCCESS:
        print(f"Failed to set mode to 0 for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
        continue
    # Set angle limits to 0 for multi-turn
    sts_comm_result, sts_error = packetHandler.write2ByteTxRx(servo_id, STS_MIN_ANGLE_LIMIT_ADDR, 0)
    if sts_comm_result != COMM_SUCCESS:
        print(f"Failed to set min angle limit for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
    sts_comm_result, sts_error = packetHandler.write2ByteTxRx(servo_id, STS_MAX_ANGLE_LIMIT_ADDR, 0)
    if sts_comm_result != COMM_SUCCESS:
        print(f"Failed to set max angle limit for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
    # Lock EEPROM
    sts_comm_result, sts_error = packetHandler.write1ByteTxRx(servo_id, STS_LOCK_ADDR, 1)
    if sts_comm_result != COMM_SUCCESS:
        print(f"Failed to lock EEPROM for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
        continue
    # Read initial position
    sts_present_position, _, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(servo_id)
    if sts_comm_result == COMM_SUCCESS and sts_error == 0:
        initial_positions[i] = sts_present_position
        print(f"Servo {servo_id} initial position: {sts_present_position}")
    else:
        print(f"Failed to read initial position for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
        initial_positions[i] = 0  # Default to 0 if reading fails
    # Enable torque
    sts_comm_result, sts_error = packetHandler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE_ADDR, 1)
    if sts_comm_result != COMM_SUCCESS:
        print(f"Failed to enable torque for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")

# GUI setup
root = tk.Tk()
root.title("STS3215 Multi-Servo Control (IDs 2-6)")
root.geometry("400x900")  # Increased size to fit five sliders, labels, and buttons

# Global variables
is_started = False  # Flag to control whether sliders send positional commands
goal_positions = [tk.IntVar(value=STS_MINIMUM_POSITION_VALUE) for _ in range(5)]
status_labels = [tk.Label(root, text=f"Servo {i+2}: Position: 0, Speed: N/A") for i in range(5)]

# Create sliders and labels for each servo (IDs 2 to 6)
for i in range(5):
    slider = tk.Scale(root, from_=STS_MINIMUM_POSITION_VALUE, to=STS_MAXIMUM_POSITION_VALUE, 
                      orient=tk.HORIZONTAL, variable=goal_positions[i], length=300, 
                      label=f"Servo {i+2} Position Offset (0-12288)")
    slider.pack(pady=5)
    status_labels[i].pack(pady=5)
    # Bind slider events to update_servo_position with the correct servo ID
    slider.bind("<Motion>", lambda event, id=i+2: update_servo_position(id))
    slider.bind("<ButtonRelease-1>", lambda event, id=i+2: update_servo_position(id))

# Function to calibrate: set current positions as zero
def calibrate():
    global initial_positions
    for i in range(5):
        servo_id = i + 2
        sts_present_position, _, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(servo_id)
        if sts_comm_result == COMM_SUCCESS and sts_error == 0:
            initial_positions[i] = sts_present_position
            print(f"Calibrated Servo {servo_id} to position: {sts_present_position}")
        else:
            print(f"Failed to read position for ID {servo_id} during calibration")

# Function to start control: enable positional commands
def start_control():
    global is_started
    is_started = True
    print("Control started")

# Function to write position to a specific servo (only if started)
def update_servo_position(servo_id):
    if not is_started:
        return  # Do not send commands until "Start" is pressed
    index = servo_id - 2  # Adjust for 0-based list index (servo 2 is index 0)
    pos = goal_positions[index].get()
    actual_pos = initial_positions[index] + pos
    sts_comm_result, sts_error = packetHandler.WritePosEx(servo_id, actual_pos, STS_MOVING_SPEED, STS_MOVING_ACC)
    if sts_comm_result != COMM_SUCCESS:
        print(f"WritePosEx error for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
    elif sts_error != 0:
        print(f"Servo error for ID {servo_id}: {packetHandler.getRxPacketError(sts_error)}")

# Function to read and update current positions and speeds for all servos
def update_status():
    while True:
        for i in range(5):
            servo_id = i + 2
            sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(servo_id)
            if sts_comm_result == COMM_SUCCESS and sts_error == 0:
                relative_position = sts_present_position - initial_positions[i]
                status_labels[i].config(text=f"Servo {servo_id}: Position: {relative_position}, Speed: {sts_present_speed}")
            else:
                status_labels[i].config(text=f"Servo {servo_id}: Error")
                print(f"ReadPosSpeed error for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
        time.sleep(0.1)  # Update every 100ms

# Start background thread for position updates
thread = Thread(target=update_status, daemon=True)
thread.start()

# Add Calibrate and Start buttons
calibrate_button = tk.Button(root, text="Calibrate", command=calibrate)
calibrate_button.pack(pady=10)
start_button = tk.Button(root, text="Start", command=start_control)
start_button.pack(pady=10)

# Cleanup on window close
def on_closing():
    for i in range(5):
        servo_id = i + 2
        packetHandler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE_ADDR, 0)  # Disable torque
    portHandler.closePort()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start GUI
root.mainloop()