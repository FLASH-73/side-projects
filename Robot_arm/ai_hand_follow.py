#!/usr/bin/env python
#
# *********     AI-Controlled Robotic Arm with 3D Hand Tracking (5 Joints)      *********
#
# Controls five STServo servos (IDs 2-6) to follow hand movements in 3D using a camera,
# with a GUI for manual control and AI mode toggle
#

import sys
import os
import tkinter as tk
from threading import Thread
import time
import cv2
import mediapipe as mp
import numpy as np
import ikpy.chain as chain
from ikpy.link import OriginLink, URDFLink

if os.name == 'nt':
    import msvcrt
else:
    import tty, termios

# Adjust path if STservo_sdk is in the same directory
sys.path.append("..")
from STservo_sdk import *  # Uses STServo SDK library

# Default settings
BAUDRATE = 1000000         # STServo default baudrate: 1 Mbps
DEVICENAME = '/dev/cu.usbserial-2140'  # Adjust for your port (e.g., COM3 on Windows)
STS_MINIMUM_POSITION_VALUE = 0
STS_MAXIMUM_POSITION_VALUE = 12288  # Multi-turn range
STS_MOVING_SPEED = 1500    # Moving speed
STS_MOVING_ACC = 50        # Moving acceleration
STS_MODE_ADDR = 33         # Mode register address
STS_TORQUE_ENABLE_ADDR = 40  # Torque enable address
STS_MIN_ANGLE_LIMIT_ADDR = 9  # Min angle limit address
STS_MAX_ANGLE_LIMIT_ADDR = 11  # Max angle limit address
STS_LOCK_ADDR = 55         # Lock register address

# Define the arm's kinematic chain (5 joints in 3D)
arm_chain = chain.Chain(name="arm", links=[
    OriginLink(),
    URDFLink(name="joint1", bounds=(-np.pi, np.pi), origin_translation=[0, 0, 0], origin_orientation=[0, 0, 0], rotation=[0, 0, 1]),
    URDFLink(name="joint2", bounds=(-np.pi, np.pi), origin_translation=[0, 0, 100], origin_orientation=[0, 0, 0], rotation=[0, 1, 0]),
    URDFLink(name="joint3", bounds=(-np.pi, np.pi), origin_translation=[0, 0, 100], origin_orientation=[0, 0, 0], rotation=[0, 1, 0]),
    URDFLink(name="joint4", bounds=(-np.pi, np.pi), origin_translation=[0, 0, 100], origin_orientation=[0, 0, 0], rotation=[0, 1, 0]),
    URDFLink(name="joint5", bounds=(-np.pi, np.pi), origin_translation=[0, 0, 100], origin_orientation=[0, 0, 0], rotation=[0, 1, 0]),
])

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
        print(f"Servo {servo_id} initial position: {sts_present_position}")
    else:
        initial_positions[i] = 0
    packetHandler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE_ADDR, 1)

# GUI setup
root = tk.Tk()
root.title("STS3215 Multi-Servo Control with AI (IDs 2-6)")
root.geometry("400x1000")

# Global variables
is_started = False  # Manual control flag
is_ai_mode = False  # AI mode flag
goal_positions = [tk.IntVar(value=STS_MINIMUM_POSITION_VALUE) for _ in range(5)]
status_labels = [tk.Label(root, text=f"Servo {i+2}: Position: 0, Speed: N/A") for i in range(5)]

# Create sliders and labels
for i in range(5):
    slider = tk.Scale(root, from_=STS_MINIMUM_POSITION_VALUE, to=STS_MAXIMUM_POSITION_VALUE, 
                      orient=tk.HORIZONTAL, variable=goal_positions[i], length=300, 
                      label=f"Servo {i+2} Position Offset (0-12288)")
    slider.pack(pady=5)
    status_labels[i].pack(pady=5)
    slider.bind("<Motion>", lambda event, id=i+2: update_servo_position(id))
    slider.bind("<ButtonRelease-1>", lambda event, id=i+2: update_servo_position(id))

# Hand tracking with MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

def hand_tracking_loop():
    global is_ai_mode
    while cap.isOpened():
        if not is_ai_mode:
            time.sleep(0.1)
            continue
        ret, frame = cap.read()
        if not ret:
            continue
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get wrist position in 3D (normalized)
                wrist = hand_landmarks.landmark[0]
                x = wrist.x
                y = wrist.y
                z = wrist.z
                # Scale to arm's workspace (e.g., ±300 mm in x, y; 0-300 mm in z)
                target_x = (x - 0.5) * 600  # Center at 0
                target_y = (0.5 - y) * 600  # Invert y-axis
                target_z = (z + 0.5) * 300  # Shift z to positive range
                # Compute IK
                target_position = [target_x, target_y, target_z]
                joint_angles = arm_chain.inverse_kinematics(target_position)
                # Convert angles to servo positions
                for i, angle in enumerate(joint_angles[1:6]):  # Skip origin link
                    pos = int((angle * 180 / np.pi + 180) * 12288 / 360)  # Radians to servo units
                    pos = max(STS_MINIMUM_POSITION_VALUE, min(STS_MAXIMUM_POSITION_VALUE, pos))
                    servo_id = i + 2
                    actual_pos = initial_positions[i] + pos
                    packetHandler.WritePosEx(servo_id, actual_pos, STS_MOVING_SPEED, STS_MOVING_ACC)
                # Draw landmarks
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        cv2.imshow('Hand Tracking', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

# Start hand tracking in a separate thread
Thread(target=hand_tracking_loop, daemon=True).start()

# Calibration function
def calibrate():
    global initial_positions
    for i in range(5):
        servo_id = i + 2
        sts_present_position, _, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(servo_id)
        if sts_comm_result == COMM_SUCCESS and sts_error == 0:
            initial_positions[i] = sts_present_position
            print(f"Calibrated Servo {servo_id} to position: {sts_present_position}")

# Start manual control
def start_control():
    global is_started
    is_started = True
    print("Manual control started")

# Toggle AI mode
def toggle_ai_mode():
    global is_ai_mode
    is_ai_mode = not is_ai_mode
    print(f"AI Mode: {'Enabled' if is_ai_mode else 'Disabled'}")
    ai_button.config(text="Disable AI" if is_ai_mode else "Enable AI")

# Update servo position (manual mode)
def update_servo_position(servo_id):
    if not is_started or is_ai_mode:
        return
    index = servo_id - 2
    pos = goal_positions[index].get()
    actual_pos = initial_positions[index] + pos
    packetHandler.WritePosEx(servo_id, actual_pos, STS_MOVING_SPEED, STS_MOVING_ACC)

# Update status display
def update_status():
    while True:
        for i in range(5):
            servo_id = i + 2
            sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(servo_id)
            if sts_comm_result == COMM_SUCCESS and sts_error == 0:
                relative_position = sts_present_position - initial_positions[i]
                status_labels[i].config(text=f"Servo {servo_id}: Pos: {relative_position}, Speed: {sts_present_speed}")
        time.sleep(0.1)

# Start status update thread
Thread(target=update_status, daemon=True).start()

# Add buttons
calibrate_button = tk.Button(root, text="Calibrate", command=calibrate)
calibrate_button.pack(pady=10)
start_button = tk.Button(root, text="Start Manual", command=start_control)
start_button.pack(pady=10)
ai_button = tk.Button(root, text="Enable AI", command=toggle_ai_mode)
ai_button.pack(pady=10)

# Cleanup on close
def on_closing():
    global is_ai_mode
    is_ai_mode = False
    for i in range(5):
        packetHandler.write1ByteTxRx(i + 2, STS_TORQUE_ENABLE_ADDR, 0)
    portHandler.closePort()
    cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start GUI
root.mainloop()