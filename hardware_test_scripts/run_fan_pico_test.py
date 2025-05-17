import serial
import time

# Replace with your Pico's serial port (e.g., '/dev/ttyACM0' on Linux, 'COM3' on Windows)
SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 115200

# Open serial connection
with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
    time.sleep(2)  # Wait for Pico to reset after opening port
    message = "on\n"
    ser.write(message.encode('utf-8'))
    print(f"Sent: {message.strip()}")


