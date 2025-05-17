import serial
import time

# Configure the serial connection
port = "/dev/ttyACM0"
baudrate = 115200
serial_connection = serial.Serial(port, baudrate)

# Read and write data until the transfer is complete

data = "on,"

serial_connection.write((str(data)).encode())
time.sleep(10)

serial_connection.close()