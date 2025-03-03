import serial
import time
import struct

class FeetechServo:
    def __init__(self, port='/dev/cu.usbserial-2140', baudrate=1000000, servo_id=1):
        self.port = port
        self.baudrate = baudrate
        self.servo_id = servo_id
        self.serial = None
        
    def connect(self):
        """Connect to the servo via serial port"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1
            )
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"Error connecting to servo: {e}")
            return False
            
    def disconnect(self):
        """Close the serial connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("Disconnected from servo")
            
    def _calculate_checksum(self, data):
        """Calculate the checksum for the data packet"""
        return (~sum(data) & 0xFF)
    
    def _send_command(self, cmd, params=None):
        """Send a command to the servo with optional parameters"""
        if params is None:
            params = []
            
        # Packet structure: 0xFF 0xFF + ID + LEN + CMD + PARAMS + CHECKSUM
        length = 3 + len(params)  # CMD(1) + PARAMS(variable) + CHECKSUM(1)
        
        data = [0xFF, 0xFF, self.servo_id, length, cmd] + params
        checksum = self._calculate_checksum(data[2:-1])  # ID through PARAMS
        data.append(checksum)
        
        try:
            self.serial.write(bytes(data))
            time.sleep(0.01)  # Short delay for processing
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def set_position(self, position, speed=0):
        """
        Set the servo position
        position: 0-4095 (0° to 360°)
        speed: 0-1000 (0 means the highest speed possible)
        """
        if not (0 <= position <= 4095):
            print("Position must be between 0 and 4095")
            return False
            
        if not (0 <= speed <= 1000):
            print("Speed must be between 0 and 1000")
            return False
            
        # SCSCL_GOAL_POSITION_L Command (0x2A)
        position_l = position & 0xFF
        position_h = (position >> 8) & 0xFF
        speed_l = speed & 0xFF
        speed_h = (speed >> 8) & 0xFF
        
        params = [position_l, position_h, speed_l, speed_h]
        return self._send_command(0x2A, params)
    
    def read_position(self):
        """Read the current position of the servo"""
        # SCSCL_PRESENT_POSITION_L Command (0x38)
        self._send_command(0x38)
        
        try:
            # Wait for response
            time.sleep(0.01)
            if self.serial.in_waiting >= 8:  # Expected response length
                response = self.serial.read(self.serial.in_waiting)
                
                # Check for header bytes
                if response[0] == 0xFF and response[1] == 0xFF:
                    # Extract position data
                    position_l = response[5]
                    position_h = response[6]
                    position = (position_h << 8) | position_l
                    return position
                    
            return None
        except Exception as e:
            print(f"Error reading position: {e}")
            return None
    
    def set_pid(self, p=16, i=0, d=0):
        """Set PID parameters for the servo"""
        if not all(0 <= param <= 255 for param in [p, i, d]):
            print("PID parameters must be between 0 and 255")
            return False
            
        # SCSCL_PID Command (0x30)
        params = [p, i, d]
        return self._send_command(0x30, params)


def main():
    # Create an instance of the servo control class
    servo = FeetechServo(port='/dev/cu.usbserial-2140', servo_id=1)
    
    # Connect to the servo
    if not servo.connect():
        print("Failed to connect to servo. Exiting.")
        return
    
    try:
        # Set PID parameters (adjust as needed)
        servo.set_pid(p=20, i=5, d=10)
        print("PID parameters set")
        
        # Move servo to different positions
        print("Moving to position 0 (0°)")
        servo.set_position(0, speed=500)
        time.sleep(2)
        
        print("Moving to position 2048 (180°)")
        servo.set_position(2048, speed=500)
        time.sleep(2)
        
        print("Moving to position 4095 (360°)")
        servo.set_position(4095, speed=500)
        time.sleep(2)
        
        # Read and display current position
        position = servo.read_position()
        if position is not None:
            print(f"Current position: {position} ({(position/4095)*360:.1f}°)")
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        # Disconnect from the servo
        servo.disconnect()

if __name__ == "__main__":
    main()