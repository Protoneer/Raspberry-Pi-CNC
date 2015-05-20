import time
import serial
import threading


class SerialConnection:
    def __init__(self, port, baud, timeout):
        self.serial_port_number = port
        self.serial_baud = baud
        self.serial_timeout = timeout

    serial_port_number = ''
    serial_baud = 0
    serial_timeout = 1

    serial_port = serial.Serial()  # config.serial_port, config.serial_baud, timeout=config.serial_timeout)

    thread = None

    def start_serial(self):
        self.serial_port.port = self.serial_port_number
        self.serial_port.baudrate = self.serial_baud
        self.serial_port.timeout = self.serial_timeout
        self.serial_port.open()
        time.sleep(4)  # Needs time to start up
        self.serial_port.flush()

    def StartSerialListener(self, dataProcessFunc):
        if self.serial_port.isOpen():
            self.serial_port.close()

        self.thread = threading.Thread(target=self.serial_port_listener, args=[dataProcessFunc])
        self.thread.daemon = True
        self.thread.start()

    def serial_port_listener(self, dataProcessFunc):
        while True:
            if not self.serial_port.isOpen():
                self.start_serial()

            if self.serial_port.inWaiting > 0:
                data = self.serial_port.readline()
                if dataProcessFunc is not None:
                    dataProcessFunc(data)

    def serial_send(self, data):
        self.serial_port.write(data)