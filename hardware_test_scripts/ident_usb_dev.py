# Example: List serial ports and try to identify Pico
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    if "Pico" in port.description or "MicroPython" in port.description:
        print(f"Pico found on {port.device}")