#!/usr/bin/env python
import os
import sys
import time

# Add the path to the STservo_sdk library
sys.path.append("..")
from STservo_sdk import *

# Servo settings
OLD_ID = 1          # Current servo ID
NEW_ID = 2          # Desired new ID
BAUDRATE = 1000000  # Baudrate for communication
DEVICENAME = '/dev/cu.usbserial-2140'  # Adjust based on your system (e.g., COM3 on Windows)
STS_LOCK_ADDR = 55  # EEPROM lock register address
STS_ID_ADDR = 5     # ID register address

# Initialize PortHandler and PacketHandler
portHandler = PortHandler(DEVICENAME)
packetHandler = sts(portHandler)

# Open the port
if not portHandler.openPort():
    print("Failed to open the port")
    sys.exit(1)
print("Port opened successfully")

# Set the baudrate
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to set the baudrate")
    portHandler.closePort()
    sys.exit(1)
print("Baudrate set successfully")

# Unlock EEPROM
print("Unlocking EEPROM...")
result, error = packetHandler.write1ByteTxRx(OLD_ID, STS_LOCK_ADDR, 0)
if result != COMM_SUCCESS:
    print(f"Failed to unlock EEPROM: {packetHandler.getTxRxResult(result)}")
    portHandler.closePort()
    sys.exit(1)
elif error != 0:
    print(f"Servo error: {packetHandler.getRxPacketError(error)}")
    portHandler.closePort()
    sys.exit(1)

# Change the ID
print(f"Changing ID from {OLD_ID} to {NEW_ID}...")
result, error = packetHandler.write1ByteTxRx(OLD_ID, STS_ID_ADDR, NEW_ID)
if result != COMM_SUCCESS:
    print(f"Failed to change ID: {packetHandler.getTxRxResult(result)}")
    portHandler.closePort()
    sys.exit(1)
elif error != 0:
    print(f"Servo error: {packetHandler.getRxPacketError(error)}")
    portHandler.closePort()
    sys.exit(1)

# Lock EEPROM
print("Locking EEPROM...")
result, error = packetHandler.write1ByteTxRx(NEW_ID, STS_LOCK_ADDR, 1)
if result != COMM_SUCCESS:
    print(f"Failed to lock EEPROM: {packetHandler.getTxRxResult(result)}")
    portHandler.closePort()
    sys.exit(1)
elif error != 0:
    print(f"Servo error: {packetHandler.getRxPacketError(error)}")
    portHandler.closePort()
    sys.exit(1)

# Verify the new ID
print(f"Verifying new ID {NEW_ID}...")
model_number, result, error = packetHandler.ping(NEW_ID)
if result == COMM_SUCCESS:
    print(f"ID change successful! New ID: {NEW_ID}, Model number: {model_number}")
else:
    print(f"Failed to verify new ID: {packetHandler.getTxRxResult(result)}")
    portHandler.closePort()
    sys.exit(1)

# Close the port
portHandler.closePort()
print("Port closed. Power cycle the servo and test the new ID.")