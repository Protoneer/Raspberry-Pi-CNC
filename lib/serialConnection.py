import time
import serial
import threading


class SerialConnection:
    def __init__(self, port, baud, timeout, processingFunc, pollFunc, pollInterval):
        self.serial_port_number = port
        self.serial_baud = baud
        self.serial_timeout = timeout
        self.dataProcessingFunction = processingFunc
        self.pollingFunction = pollFunc
        self.polling_interval = pollInterval

    serial_port_number = ''
    serial_baud = 0
    serial_timeout = 1

    serial_port = serial.Serial()  # config.serial_port, config.serial_baud, timeout=config.serial_timeout)

    thread = None

    dataProcessingFunction = None

    pollingFunction = None
    polling_interval = 250

    def start_serial(self):
        self.serial_port.port = self.serial_port_number
        self.serial_port.baudrate = self.serial_baud
        self.serial_port.timeout = self.serial_timeout
        self.serial_port.open()
        time.sleep(4)  # Needs time to start up
        self.serial_port.flush()

    def StartSerialListener(self):
        if self.serial_port.isOpen():
            self.serial_port.close()

        self.thread = threading.Thread(target=self.serial_port_listener,
                                       args=())
        self.thread.start()

    def serial_port_listener(self):
        lastPoleTime = int(round(time.time() * 1000)) + 6000
        while True:

            if not self.serial_port.isOpen():
                self.start_serial()

            if self.serial_port.inWaiting > 0:
                data = self.serial_port.readline()
                if self.dataProcessingFunction is not None:
                    self.dataProcessingFunction(data)

            if self.polling_interval > 0 and int(round(time.time() * 1000)) > lastPoleTime + self.polling_interval:
                lastPoleTime = int(round(time.time() * 1000))
                if self.pollingFunction is not None:
                    self.pollingFunction(self.serial_port)

    def serial_send(self, data):
        self.serial_port.write(data)

    def StopSerialListener(self):
        self.serial_port.close()
        self.thread.stop()
