import serial
import time

# Configure the serial connection
port = "/dev/ttyACM0"
baudrate = 115200
ser = serial.Serial(port, baudrate)

# Read and write data until the transfer is complete

command = "on\n"
ser.write(command.encode('ascii'))  # Encode as ASCII and send

time.sleep(10)

ser.close()