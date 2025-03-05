#!/usr/bin/env python
#
# *********     GUI Servo Control Example      *********
#
# Controls STServo position with a slider (0-4095) and displays current position
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
STS_ID = 4                 # STServo ID: 1
BAUDRATE = 1000000         # STServo default baudrate: 1 Mbps
DEVICENAME = '/dev/cu.usbserial-2140'  # Your Mac port
STS_MINIMUM_POSITION_VALUE = 0
STS_MAXIMUM_POSITION_VALUE = 12288
STS_MOVING_SPEED = 9000    # Moving speed
STS_MOVING_ACC = 50        # Moving acceleration

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

# GUI setup
root = tk.Tk()
root.title("STS3215 Servo Control")
root.geometry("400x200")

# Global variable for goal position
goal_position = tk.IntVar(value=STS_MINIMUM_POSITION_VALUE)

# Slider to control position
slider = tk.Scale(root, from_=STS_MINIMUM_POSITION_VALUE, to=STS_MAXIMUM_POSITION_VALUE, 
                  orient=tk.HORIZONTAL, variable=goal_position, length=300, 
                  label="Servo Position (0-4095)")
slider.pack(pady=20)

# Label to display current position and speed
status_label = tk.Label(root, text="Current Position: N/A, Speed: N/A")
status_label.pack(pady=10)

# Function to write position to servo
def update_servo_position(*args):
    pos = goal_position.get()
    sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, pos, STS_MOVING_SPEED, STS_MOVING_ACC)
    if sts_comm_result != COMM_SUCCESS:
        print(f"WritePosEx error: {packetHandler.getTxRxResult(sts_comm_result)}")
    elif sts_error != 0:
        print(f"Servo error: {packetHandler.getRxPacketError(sts_error)}")

# Function to read and update current position continuously
def update_status():
    while True:
        sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(STS_ID)
        if sts_comm_result == COMM_SUCCESS and sts_error == 0:
            status_label.config(text=f"Current Position: {sts_present_position}, Speed: {sts_present_speed}")
        else:
            status_label.config(text="Error reading position")
            print(f"ReadPosSpeed error: {packetHandler.getTxRxResult(sts_comm_result)}")
        time.sleep(0.1)  # Update every 100ms

# Bind slider movement to servo update
slider.bind("<Motion>", update_servo_position)  # Update on drag
slider.bind("<ButtonRelease-1>", update_servo_position)  # Ensure update on release

# Start background thread for position updates
thread = Thread(target=update_status, daemon=True)
thread.start()

# Cleanup on window close
def on_closing():
    portHandler.closePort()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start GUI
root.mainloop()