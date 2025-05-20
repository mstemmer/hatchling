import serial
import time


def fan_control(duty_cycle):
    # Configure the serial connection
    port = "/dev/ttyACM0"
    baudrate = 115200
    serial_connection = serial.Serial(port, baudrate)
    serial_connection.write(f"{duty_cycle}\n".encode("ascii"))

    time.sleep(1)

    serial_connection.close()
