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
STS_MINIMUM_POSITION_VALUE = 0
STS_MAXIMUM_POSITION_VALUE = 8190  # 2 turns (720°)
STS_MOVING_SPEED = 2400  # Speed in steps per second
STS_MOVING_ACC = 50      # Acceleration
STS_MODE_ADDR = 33       # Mode register address
STS_TORQUE_ENABLE_ADDR = 40  # Torque enable address
STS_MIN_ANGLE_LIMIT_ADDR = 9  # Min angle limit address
STS_MAX_ANGLE_LIMIT_ADDR = 11  # Max angle limit address
STS_LOCK_ADDR = 55        # Lock register address

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

# Unlock the servo
print("Unlocking servo...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_LOCK_ADDR, 0)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to unlock servo: {packetHandler.getTxRxResult(sts_comm_result)}")
    portHandler.closePort()
    sys.exit(1)
elif sts_error != 0:
    print(f"Servo error on unlock: {packetHandler.getRxPacketError(sts_error)}")

# Disable torque
print("Disabling torque...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_TORQUE_ENABLE_ADDR, 0)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to disable torque: {packetHandler.getTxRxResult(sts_comm_result)}")
    portHandler.closePort()
    sys.exit(1)
elif sts_error != 0:
    print(f"Servo error on disable torque: {packetHandler.getRxPacketError(sts_error)}")

# Set servo to Position Mode (Mode 0)
print("Setting position mode (STS_MODE = 0)...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_MODE_ADDR, 0)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to set mode: {packetHandler.getTxRxResult(sts_comm_result)}")
    portHandler.closePort()
    sys.exit(1)
elif sts_error != 0:
    print(f"Servo error: {packetHandler.getRxPacketError(sts_error)}")
    portHandler.closePort()
    sys.exit(1)

# Verify mode
mode_value, mode_result, mode_error = packetHandler.read1ByteTxRx(STS_ID, STS_MODE_ADDR)
if mode_result == COMM_SUCCESS:
    print(f"Mode set to: {mode_value}")
    if mode_value != 0:
        print("Mode did not change to 0, multi-turn may not work as expected")
else:
    print(f"Failed to read mode: {packetHandler.getTxRxResult(mode_result)}")

# Read current angle limits before setting
print("Reading current angle limits...")
min_limit_raw, min_result, min_error = packetHandler.read2ByteTxRx(STS_ID, STS_MIN_ANGLE_LIMIT_ADDR)
max_limit_raw, max_result, max_error = packetHandler.read2ByteTxRx(STS_ID, STS_MAX_ANGLE_LIMIT_ADDR)
if min_result == COMM_SUCCESS and max_result == COMM_SUCCESS:
    min_limit = packetHandler.sts_tohost(min_limit_raw, 15)
    max_limit = packetHandler.sts_tohost(max_limit_raw, 15)
    print(f"Current angle limits: {min_limit} to {max_limit}")
else:
    print("Failed to read current angle limits")

# Set angle limits for multi-turn (±2 turns to match slider range)
min_angle_limit = -8192  # -2 turns
max_angle_limit = 8192   # +2 turns
print("Setting min angle limit to", min_angle_limit)
sts_comm_result, sts_error = packetHandler.write2ByteTxRx(STS_ID, STS_MIN_ANGLE_LIMIT_ADDR, min_angle_limit)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to set min angle limit: {packetHandler.getTxRxResult(sts_comm_result)}")
elif sts_error != 0:
    print(f"Servo error on min limit: {packetHandler.getRxPacketError(sts_error)}")

print("Setting max angle limit to", max_angle_limit)
sts_comm_result, sts_error = packetHandler.write2ByteTxRx(STS_ID, STS_MAX_ANGLE_LIMIT_ADDR, max_angle_limit)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to set max angle limit: {packetHandler.getTxRxResult(sts_comm_result)}")
elif sts_error != 0:
    print(f"Servo error on max limit: {packetHandler.getRxPacketError(sts_error)}")

# Verify angle limits after setting
print("Verifying angle limits...")
min_limit_raw, min_result, min_error = packetHandler.read2ByteTxRx(STS_ID, STS_MIN_ANGLE_LIMIT_ADDR)
max_limit_raw, max_result, max_error = packetHandler.read2ByteTxRx(STS_ID, STS_MAX_ANGLE_LIMIT_ADDR)
if min_result == COMM_SUCCESS and max_result == COMM_SUCCESS:
    min_limit = packetHandler.sts_tohost(min_limit_raw, 15)
    max_limit = packetHandler.sts_tohost(max_limit_raw, 15)
    print(f"Angle limits set to: {min_limit} to {max_limit}")
    if min_limit != min_angle_limit or max_limit != max_angle_limit:
        print("Warning: Angle limits did not set as expected!")
else:
    print("Failed to read angle limits")

# Enable torque
print("Enabling torque...")
sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_TORQUE_ENABLE_ADDR, 1)
if sts_comm_result != COMM_SUCCESS:
    print(f"Failed to enable torque: {packetHandler.getTxRxResult(sts_comm_result)}")
    portHandler.closePort()
    sys.exit(1)
elif sts_error != 0:
    print(f"Servo error: {packetHandler.getRxPacketError(sts_error)}")
    portHandler.closePort()
    sys.exit(1)

# Lock for serial port access
port_lock = Lock()

# GUI setup
root = tk.Tk()
root.title("STS3215 Servo Control (Two Spins)")
root.geometry("400x200")

goal_position = tk.IntVar(value=STS_MINIMUM_POSITION_VALUE)

slider = tk.Scale(root, from_=STS_MINIMUM_POSITION_VALUE, to=STS_MAXIMUM_POSITION_VALUE, 
                  orient=tk.HORIZONTAL, variable=goal_position, length=300, 
                  label="Servo Position (0-8190 for 720°)")
slider.pack(pady=20)

status_label = tk.Label(root, text="Current Position: N/A, Speed: N/A")
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
        sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(STS_ID)
        if sts_comm_result == COMM_SUCCESS and sts_error == 0:
            status_label.config(text=f"Current Position: {sts_present_position}, Speed: {sts_present_speed}")
        else:
            status_label.config(text="Error reading position")
            print(f"ReadPosSpeed error: {packetHandler.getTxRxResult(sts_comm_result)}")
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