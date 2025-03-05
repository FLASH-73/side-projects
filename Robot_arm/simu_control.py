#!/usr/bin/env python
#
# *********     GUI Multi-Servo Control with 3D Simulation      *********
#
# Controls five STServo servos (IDs 2-6) via a 3D simulation in PyBullet
#

import sys
import os
import tkinter as tk
from threading import Thread
import time
import queue
import pybullet as p
import pybullet_data

if os.name == 'nt':
    import msvcrt
else:
    import tty, termios

# Adjust path if STservo_sdk is in the same directory
sys.path.append("..")
from STservo_sdk import *

# Default settings
BAUDRATE = 1000000
DEVICENAME = '/dev/cu.usbserial-2140'
STS_MINIMUM_POSITION_VALUE = 0
STS_MAXIMUM_POSITION_VALUE = 12288
STS_MOVING_SPEED = 1500
STS_MOVING_ACC = 50
STS_MODE_ADDR = 33
STS_TORQUE_ENABLE_ADDR = 40
STS_MIN_ANGLE_LIMIT_ADDR = 9
STS_MAX_ANGLE_LIMIT_ADDR = 11
STS_LOCK_ADDR = 55

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

# Initialize servos
initial_positions = [0] * 5
for i in range(5):
    servo_id = i + 2
    packetHandler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE_ADDR, 0)
    packetHandler.write1ByteTxRx(servo_id, STS_LOCK_ADDR, 0)
    packetHandler.write1ByteTxRx(servo_id, STS_MODE_ADDR, 0)
    packetHandler.write2ByteTxRx(servo_id, STS_MIN_ANGLE_LIMIT_ADDR, 0)
    packetHandler.write2ByteTxRx(servo_id, STS_MAX_ANGLE_LIMIT_ADDR, 0)
    packetHandler.write1ByteTxRx(servo_id, STS_LOCK_ADDR, 1)
    sts_present_position, _, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(servo_id)
    if sts_comm_result == COMM_SUCCESS and sts_error == 0:
        initial_positions[i] = sts_present_position
    else:
        initial_positions[i] = 0
    packetHandler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE_ADDR, 1)

# Queue for joint positions
position_queue = queue.Queue()

# PyBullet simulation thread
def pybullet_thread():
    p.connect(p.GUI)  # Open PyBullet GUI
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    robot_id = p.loadURDF("path/to/your/robot.urdf")  # Update this path
    p.setRealTimeSimulation(1)
    
    num_joints = p.getNumJoints(robot_id)
    print(f"Loaded robot with {num_joints} joints")
    
    while True:
        joint_states = []
        for i in range(min(5, num_joints)):  # Match your 5 servos
            pos, _, _, _ = p.getJointState(robot_id, i)
            joint_states.append(pos)  # Position in radians
        position_queue.put(joint_states)
        time.sleep(0.01)  # 100 Hz update rate

# Start PyBullet thread
Thread(target=pybullet_thread, daemon=True).start()

# GUI setup
root = tk.Tk()
root.title("STS3215 Servo Control with 3D Simulation")
root.geometry("400x300")

status_labels = [tk.Label(root, text=f"Servo {i+2}: Position: 0, Speed: N/A") for i in range(5)]
for i in range(5):
    status_labels[i].pack(pady=5)

# Update servos from simulation
def update_servos_from_simulation():
    try:
        joint_states = position_queue.get_nowait()
        for i, servo_id in enumerate(range(2, 7)):
            if i < len(joint_states):
                # Convert radians to servo units (0-12288 for 0-360 degrees)
                pos_rad = joint_states[i]
                pos_servo = int((pos_rad + 3.14159) / (2 * 3.14159) * 12288)  # Map -pi to pi to 0-12288
                pos_servo = max(STS_MINIMUM_POSITION_VALUE, min(STS_MAXIMUM_POSITION_VALUE, pos_servo))
                sts_comm_result, sts_error = packetHandler.WritePosEx(servo_id, pos_servo, STS_MOVING_SPEED, STS_MOVING_ACC)
                if sts_comm_result != COMM_SUCCESS:
                    print(f"WritePosEx error for ID {servo_id}: {packetHandler.getTxRxResult(sts_comm_result)}")
    except queue.Empty:
        pass
    root.after(10, update_servos_from_simulation)

# Update status labels
def update_status():
    while True:
        for i in range(5):
            servo_id = i + 2
            pos, speed, comm_result, error = packetHandler.ReadPosSpeed(servo_id)
            if comm_result == COMM_SUCCESS and error == 0:
                relative_position = pos - initial_positions[i]
                status_labels[i].config(text=f"Servo {servo_id}: Position: {relative_position}, Speed: {speed}")
        time.sleep(0.1)

# Start threads
Thread(target=update_status, daemon=True).start()
root.after(10, update_servos_from_simulation)

# Cleanup
def on_closing():
    for i in range(5):
        packetHandler.write1ByteTxRx(i + 2, STS_TORQUE_ENABLE_ADDR, 0)
    portHandler.closePort()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()