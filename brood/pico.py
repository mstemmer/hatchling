import serial
import time
import logging


def fan_control(duty_cycle):
    """Control fan speed via Pico microcontroller"""
    port = "/dev/ttyACM0"
    baudrate = 115200
    
    try:
        serial_connection = serial.Serial(port, baudrate, timeout=2)
        serial_connection.write(f"{duty_cycle}\n".encode("ascii"))
        time.sleep(1)
        serial_connection.close()
        logging.info(f"Fan control: set duty cycle to {duty_cycle}%")
    except serial.SerialException as e:
        logging.error(f"Failed to connect to Pico for fan control: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error in fan_control: {str(e)}")


def move_eggs():
    """Move eggs via Pico microcontroller"""
    port = "/dev/ttyACM0"
    baudrate = 115200
    
    try:
        serial_connection = serial.Serial(port, baudrate, timeout=2)
        serial_connection.write('move_eggs\n'.encode("ascii"))
        time.sleep(1)
        serial_connection.close()
        logging.info("Turning eggs")
    except serial.SerialException as e:
        logging.error(f"Failed to connect to Pico for egg movement: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error in move_eggs: {str(e)}")