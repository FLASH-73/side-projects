#!/usr/bin/env python
#
# *********     GUI Servo Control Example (Multi-Turn Enabled)      *********
#

import sys
import os
import tkinter as tk
from threading import Lock
import time

if os.name == 'nt':
    import msvcrt
else:
    import tty, termios

sys.path.append("..")
from STservo_sdk import *

# Default settings
STS_ID = 2
BAUDRATE = 1000000
DEVICENAME = '/dev/cu.usbserial-2140'
STS_MINIMUM_POSITION_VALUE = 0  # -2 turns
STS_MAXIMUM_POSITION_VALUE = 12288   # +2 turns (adjustable up to ±28672 for ±7 turns)
STS_MOVING_SPEED = 2400  # Speed in steps per second
STS_MOVING_ACC = 50      # Acceleration
STS_MODE_ADDR = 33       # Mode register address
STS_TORQUE_ENABLE_ADDR = 40  # Torque enable address
STS_MIN_ANGLE_LIMIT_ADDR = 9  # Min angle limit address
STS_MAX_ANGLE_LIMIT_ADDR = 11  # Max angle limit address
STS_LOCK_ADDR = 55        # Lock register address
STS_STATUS_ADDR = 65      # Servo status address

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

# Ping to confirm servo
model_number, ping_result, ping_error = packetHandler.ping(STS_ID)
if ping_result == COMM_SUCCESS:
    print(f"Ping successful! Model number: {model_number}")
else:
    print(f"Ping failed: {packetHandler.getTxRxResult(ping_result)}")
    portHandler.closePort()
    sys.exit(1)

# Unlock the servo EEPROM
print("Unlocking servo EEPROM...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_LOCK_ADDR, 0)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to unlock EEPROM: {packetHandler.getTxRxResult(sts_comm_result)}")
    sys.exit(1)
elif sts_error != 0:
    print(f"Servo error on unlock: {packetHandler.getRxPacketError(sts_error)}")

# Disable torque
print("Disabling torque...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_TORQUE_ENABLE_ADDR, 0)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to disable torque: {packetHandler.getTxRxResult(sts_comm_result)}")
    sys.exit(1)
elif sts_error != 0:
    print(f"Servo error on disable torque: {packetHandler.getRxPacketError(sts_error)}")

# Set servo to Position Mode (Mode 0)
print("Setting position mode (STS_MODE = 0)...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_MODE_ADDR, 0)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to set mode: {packetHandler.getTxRxResult(sts_comm_result)}")
    sys.exit(1)
elif sts_error != 0:
    print(f"Servo error: {packetHandler.getRxPacketError(sts_error)}")
    sys.exit(1)

# Verify mode
mode_value, mode_result, mode_error = packetHandler.read1ByteTxRx(STS_ID, STS_MODE_ADDR)
if mode_result == COMM_SUCCESS:
    print(f"Mode set to: {mode_value}")
    if mode_value != 0:
        print("Mode did not change to 0, multi-turn may not work as expected")
else:
    print(f"Failed to read mode: {packetHandler.getTxRxResult(mode_result)}")

# Set angle limits to 0 for multi-turn control
min_angle_limit = 0
max_angle_limit = 0
print("Setting min angle limit to 0 for multi-turn...")
sts_comm_result, sts_error = packetHandler.write2ByteTxRx(STS_ID, STS_MIN_ANGLE_LIMIT_ADDR, min_angle_limit)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to set min angle limit: {packetHandler.getTxRxResult(sts_comm_result)}")
elif sts_error != 0:
    print(f"Servo error on min limit: {packetHandler.getRxPacketError(sts_error)}")

print("Setting max angle limit to 0 for multi-turn...")
sts_comm_result, sts_error = packetHandler.write2ByteTxRx(STS_ID, STS_MAX_ANGLE_LIMIT_ADDR, max_angle_limit)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to set max angle limit: {packetHandler.getTxRxResult(sts_comm_result)}")
elif sts_error != 0:
    print(f"Servo error on max limit: {packetHandler.getRxPacketError(sts_error)}")

# Verify angle limits
print("Verifying angle limits...")
min_limit_raw, min_result, min_error = packetHandler.read2ByteTxRx(STS_ID, STS_MIN_ANGLE_LIMIT_ADDR)
max_limit_raw, max_result, max_error = packetHandler.read2ByteTxRx(STS_ID, STS_MAX_ANGLE_LIMIT_ADDR)
if min_result == COMM_SUCCESS and max_result == COMM_SUCCESS:
    min_limit = packetHandler.sts_tohost(min_limit_raw, 15)
    max_limit = packetHandler.sts_tohost(max_limit_raw, 15)
    print(f"Angle limits set to: {min_limit} to {max_limit}")
    if min_limit != 0 or max_limit != 0:
        print("Warning: Angle limits did not set to 0 as expected!")
else:
    print("Failed to read angle limits")

# Lock the EEPROM to save changes
print("Locking EEPROM...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_LOCK_ADDR, 1)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to lock EEPROM: {packetHandler.getTxRxResult(sts_comm_result)}")
elif sts_error != 0:
    print(f"Servo error on lock: {packetHandler.getRxPacketError(sts_error)}")

# Enable torque
print("Enabling torque...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_TORQUE_ENABLE_ADDR, 1)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to enable torque: {packetHandler.getTxRxResult(sts_comm_result)}")
    sys.exit(1)
elif sts_error != 0:
    print(f"Servo error: {packetHandler.getRxPacketError(sts_error)}")
    sys.exit(1)

# Lock for serial port access
port_lock = Lock()

# GUI setup
root = tk.Tk()
root.title("STS3215 Servo Control (Multi-Turn)")
root.geometry("400x200")

goal_position = tk.IntVar(value=0)

slider = tk.Scale(root, from_=STS_MINIMUM_POSITION_VALUE, to=STS_MAXIMUM_POSITION_VALUE, 
                  orient=tk.HORIZONTAL, variable=goal_position, length=300, 
                  label="Servo Position (0 to 12288)")
slider.pack(pady=20)

status_label = tk.Label(root, text="Current Position: N/A, Speed: N/A, Status: N/A")
status_label.pack(pady=10)

# Function to update servo position
def update_servo_position(*args):
    pos = goal_position.get()
    print(f"Setting position to {pos}")
    with port_lock:
        sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, pos, STS_MOVING_SPEED, STS_MOVING_ACC)
        if sts_comm_result != COMM_SUCCESS:
            print(f"WritePosEx error: {packetHandler.getTxRxResult(sts_comm_result)}")
        elif sts_error != 0:
            print(f"Servo error: {packetHandler.getRxPacketError(sts_error)}")

# Function to read servo status and update GUI
def read_and_update_status():
    with port_lock:
        # Read position and speed
        sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(STS_ID)
        # Read servo status
        status_value, status_result, status_error = packetHandler.read1ByteTxRx(STS_ID, STS_STATUS_ADDR)
        
        if sts_comm_result == COMM_SUCCESS and sts_error == 0 and status_result == COMM_SUCCESS:
            status_text = f"Current Position: {sts_present_position}, Speed: {sts_present_speed}, Status: {status_value}"
            status_label.config(text=status_text)
            if status_value != 0:
                print(f"Servo status error detected: {status_value}")
        else:
            status_label.config(text="Error reading position or status")
            print(f"ReadPosSpeed error: {packetHandler.getTxRxResult(sts_comm_result)} or Status error: {packetHandler.getTxRxResult(status_result)}")
    root.after(100, read_and_update_status)

# Bind slider to update position on release
slider.bind("<ButtonRelease-1>", update_servo_position)

# Start periodic status updates
read_and_update_status()

# Cleanup on window close
def on_closing():
    with port_lock:
        packetHandler.write1ByteTxRx(STS_ID, STS_TORQUE_ENABLE_ADDR, 0)  # Disable torque
    portHandler.closePort()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()