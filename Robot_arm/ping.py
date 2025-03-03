#!/usr/bin/env python
#
# *********     Ping Example      *********
#
# Available STServo model: All models using Protocol STS
# Tested with STServo and FE-URT-1 on macOS
#

import sys
import os

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

#sys.path.append("..")
from STservo_sdk import *  # Ensure this is in the parent directory or installed

# Default setting
STS_ID = 1                 # STServo ID: 1 (default)
BAUDRATE = 1000000         # STServo default baudrate: 1 Mbps
DEVICENAME = '/dev/cu.usbserial-2140'  # Your Mac port for FE-URT-1

# Initialize PortHandler instance
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
packetHandler = sts(portHandler)

# Open port
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()

# Set port baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

# Ping the STServo
sts_model_number, sts_comm_result, sts_error = packetHandler.ping(STS_ID)
if sts_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(sts_comm_result))
else:
    print("[ID:%03d] ping Succeeded. STServo model number: %d" % (STS_ID, sts_model_number))
if sts_error != 0:
    print("%s" % packetHandler.getRxPacketError(sts_error))















































































    

# Close port
portHandler.closePort()