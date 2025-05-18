import serial
import time



# Configure the serial connection
port = "/dev/ttyACM0"
baudrate = 115200
serial_connection = serial.Serial(port, baudrate)

# Read and write data until the transfer is complete

# serial_connection.write(('led_on\n').encode())
serial_connection.write((b'led_off\n'))
# serial_connection.write(f"{50}\n".encode("ascii"))

time.sleep(1)

serial_connection.close()