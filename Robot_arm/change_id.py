from STservo_sdk import *

# Initialize port and packet handler
portHandler = PortHandler('/dev/cu.usbserial-2140')  # Update to your port
packetHandler = sts(portHandler)

# Open port
if not portHandler.openPort():
    print("Failed to open port")
    exit(1)

# Set baudrate (match your servo's baudrate, e.g., 1000000)
if not portHandler.setBaudRate(1000000):
    print("Failed to set baudrate")
    portHandler.closePort()
    exit(1)

# Change ID from 1 to 2
new_id = 2
result, error = packetHandler.write1ByteTxRx(1, 5, new_id)  # Address 5 is STS_ID
if result == COMM_SUCCESS and error == 0:
    print(f"Servo ID changed to {new_id}")
else:
    print(f"Failed to change ID: {packetHandler.getTxRxResult(result)}")

# Close port
portHandler.closePort()