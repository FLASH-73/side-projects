import serial
import time

def calculate_checksum(packet):
    checksum = 0
    for byte in packet[2:-1]:
        checksum += byte
    return (~checksum) & 0xFF

def create_move_packet(servo_id, position, move_time=1000):
    pos_low = position & 0xFF
    pos_high = (position >> 8) & 0xFF
    time_low = move_time & 0xFF
    time_high = (move_time >> 8) & 0xFF
    packet = [0xFF, 0xFF, servo_id, 0x07, 0x03, pos_low, pos_high, time_low, time_high]
    checksum = calculate_checksum(packet)
    packet.append(checksum)
    return bytearray(packet)

def create_torque_packet(servo_id, enable=1):
    packet = [0xFF, 0xFF, servo_id, 0x04, 0x03, 0x40, enable]
    checksum = calculate_checksum(packet)
    packet.append(checksum)
    return bytearray(packet)

def test_servo(port):
    try:
        ser = serial.Serial(port=port, baudrate=38400, timeout=1)
        print(f"Connected to {ser.portstr}")

        # Sweep positions to test
        for pos in [0, 2048, 4000]:
            for servo_id in [1, 254]:
                print(f"\nTesting ID {servo_id} at position {pos}")
                ser.write(create_torque_packet(servo_id, 1))
                ser.write(create_move_packet(servo_id, pos))
                time.sleep(1)  # Wait for movement
        ser.close()
        print("Port closed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    port_name = "/dev/cu.usbserial-2140"
    test_servo(port_name)