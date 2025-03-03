#!/usr/bin/env python
#
# *********     Multi-Servo GUI Control with Independent ID Selection and Setting      *********
#
# Controls three STServos independently with sliders, sets IDs, selects control IDs, and displays positions
# Tested with STServo and FE-URT-1 on macOS
#

import sys
import os
import tkinter as tk
from threading import Thread, Lock
import time

if os.name == 'nt':
    import msvcrt
else:
    import tty, termios

# Adjust path if STservo_sdk is in the same directory
sys.path.append("..")
from STservo_sdk import *  # Uses STServo SDK library

# Default settings
DEFAULT_ID = 1
BAUDRATE = 1000000         # STServo default baudrate: 1 Mbps
DEVICENAME = '/dev/cu.usbserial-2140'  # Your Mac port
STS_MINIMUM_POSITION_VALUE = 0
STS_MAXIMUM_POSITION_VALUE = 4095
STS_MOVING_SPEED = 2400    # Moving speed
STS_MOVING_ACC = 50        # Moving acceleration
STS_ID_MIN = 0             # Min ID
STS_ID_MAX = 253           # Max ID

# Initialize PortHandler and PacketHandler
portHandler = PortHandler(DEVICENAME)
packetHandler = sts(portHandler)

# Global lock for thread-safe access to packetHandler
packet_lock = Lock()

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
root.title("Multi-Servo Control")
root.geometry("400x700")  # Increased height for three sliders

# Function to create a slider frame
def create_slider_frame(slider_num):
    frame = tk.Frame(root)
    frame.pack(pady=10, padx=10, fill='x')

    # Servo ID for this slider
    servo_id = tk.IntVar(value=DEFAULT_ID)

    # Label for the currently controlled servo ID
    id_label = tk.Label(frame, text=f"Slider {slider_num} Controlling Servo ID: {servo_id.get()}")
    id_label.pack(pady=5)

    # Slider to control position
    goal_position = tk.IntVar(value=STS_MINIMUM_POSITION_VALUE)
    slider = tk.Scale(frame, from_=STS_MINIMUM_POSITION_VALUE, to=STS_MAXIMUM_POSITION_VALUE, 
                      orient=tk.HORIZONTAL, variable=goal_position, length=300, 
                      label=f"Servo {slider_num} Position (0-4095)")
    slider.pack(pady=5)

    # Label to display current position and speed
    status_label = tk.Label(frame, text="Current Position: N/A, Speed: N/A")
    status_label.pack(pady=5)

    # Entry box and button to select the servo ID to control
    control_id_label = tk.Label(frame, text="Select Servo ID to Control (0-253):")
    control_id_label.pack(pady=5)
    control_id_entry = tk.Entry(frame, width=10)
    control_id_entry.pack(pady=5)
    control_id_entry.insert(0, str(servo_id.get()))  # Default value

    # Function to set the control ID for this slider
    def set_control_id():
        with packet_lock:
            try:
                control_id_str = control_id_entry.get()
                print(f"Slider {slider_num}: Entered control ID: '{control_id_str}'")
                control_id = int(control_id_str)
                if STS_ID_MIN <= control_id <= STS_ID_MAX:
                    print(f"Slider {slider_num}: Pinging ID {control_id}...")
                    _, ping_result, ping_error = packetHandler.ping(control_id)
                    print(f"Slider {slider_num}: Ping result: {ping_result}, error: {ping_error}")
                    if ping_result == COMM_SUCCESS and ping_error == 0:
                        servo_id.set(control_id)
                        id_label.config(text=f"Slider {slider_num} Controlling Servo ID: {control_id}")
                        print(f"Slider {slider_num} now controlling servo ID {control_id}")
                    else:
                        print(f"Servo ID {control_id} not responding")
                else:
                    print(f"ID {control_id} is out of range ({STS_ID_MIN}-{STS_ID_MAX})")
            except ValueError:
                print("Please enter a valid integer ID")

    set_control_id_button = tk.Button(frame, text="Set Control ID", command=set_control_id)
    set_control_id_button.pack(pady=5)

    # Entry box and button to change the servo's ID
    change_id_label = tk.Label(frame, text="Change ID of Current Servo (0-253):")
    change_id_label.pack(pady=5)
    change_id_entry = tk.Entry(frame, width=10)
    change_id_entry.pack(pady=5)
    change_id_entry.insert(0, str(servo_id.get()))  # Default value

    # Function to change the servo's ID for this slider
    def set_id():
        with packet_lock:
            try:
                new_id_str = change_id_entry.get()
                print(f"Slider {slider_num}: Entered new ID: '{new_id_str}'")
                new_id = int(new_id_str)
                if STS_ID_MIN <= new_id <= STS_ID_MAX:
                    print(f"Slider {slider_num}: Changing ID of servo {servo_id.get()} to {new_id}")
                    sts_comm_result, sts_error = packetHandler.write1ByteTxRx(servo_id.get(), 5, new_id)
                    if sts_comm_result == COMM_SUCCESS and sts_error == 0:
                        print(f"Slider {slider_num}: Verifying new ID {new_id}")
                        _, ping_result, ping_error = packetHandler.ping(new_id)
                        if ping_result == COMM_SUCCESS and ping_error == 0:
                            servo_id.set(new_id)  # Update this slider's control ID
                            id_label.config(text=f"Slider {slider_num} Controlling Servo ID: {new_id}")
                            print(f"Slider {slider_num} servo ID changed to {new_id}")
                        else:
                            print(f"Failed to verify new ID {new_id} via ping")
                    else:
                        print(f"write1ByteTxRx failed: {packetHandler.getTxRxResult(sts_comm_result)}")
                else:
                    print(f"ID {new_id} is out of range ({STS_ID_MIN}-{STS_ID_MAX})")
            except ValueError:
                print("Please enter a valid integer ID")

    set_id_button = tk.Button(frame, text="Set Servo ID", command=set_id)
    set_id_button.pack(pady=5)

    # Function to write position to servo
    def update_servo_position(*args):
        
        with packet_lock:
            pos = goal_position.get()
            sts_comm_result, sts_error = packetHandler.WritePosEx(servo_id.get(), pos, STS_MOVING_SPEED, STS_MOVING_ACC)
            if sts_comm_result != COMM_SUCCESS:
                print(f"WritePosEx error: {packetHandler.getTxRxResult(sts_comm_result)}")
            elif sts_error != 0:
                print(f"Servo error: {packetHandler.getRxPacketError(sts_error)}")

    # Function to read and update current position continuously
    def update_status():
        while True:
            if packet_lock.acquire(blocking=False):  # Try to acquire lock without blocking
                try:
                    sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(servo_id.get())
                    if sts_comm_result == COMM_SUCCESS and sts_error == 0:
                        status_label.config(text=f"Current Position: {sts_present_position}, Speed: {sts_present_speed}")
                    else:
                        status_label.config(text="Error reading position")
                        print(f"ReadPosSpeed error for ID {servo_id.get()}: {packetHandler.getTxRxResult(sts_comm_result)}")
                except Exception as e:
                    print(f"Exception in update_status for slider {slider_num}: {e}")
                finally:
                    packet_lock.release()  # Always release the lock if acquired
            # Optional: Uncomment to debug skipped updates
            # else:
            #     print(f"Slider {slider_num}: Skipped status update due to lock")
            time.sleep(0.2)  # Increase to 0.2s for less frequent updates

    # Bind slider movement to servo update
    slider.bind("<Motion>", update_servo_position)  # Update on drag
    slider.bind("<ButtonRelease-1>", update_servo_position)  # Ensure update on release

    # Start background thread for position updates
    thread = Thread(target=update_status, daemon=True)
    thread.start()

    return frame

# Create three slider frames
for i in range(1, 4):
    create_slider_frame(i)

# Cleanup on window close
def on_closing():
    portHandler.closePort()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start GUI
root.mainloop()