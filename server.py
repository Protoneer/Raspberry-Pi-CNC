from gevent import monkey

monkey.patch_all()

from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect

import threading
import serial
import time
import datetime
import sys


app = Flask(__name__, static_url_path='')
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)




class Machine:
    status = ''
    mpos_x = 0
    mpos_y = 0
    mpos_z = 0
    wpos_x = 0
    wpos_y = 0
    wpos_z = 0

    def parseData(self,data):
        fields = str(data).replace("<", "").replace(">", "").replace("MPos:", "").replace("WPos:", "")\
            .replace("\r\n", "").split(",")

        self.status = fields[0]
        self.mpos_x = fields[1]
        self.mpos_y = fields[2]
        self.mpos_z = fields[3]
        self.wpos_x = fields[4]
        self.wpos_y = fields[5]
        self.wpos_z = fields[6]


##### Config #####

port = '/dev/ttyUSB0'
baud = 115200
timeout = 0.1
serial_port = serial.Serial(port, baud, timeout=timeout)
poll_interval = 250  # Disabled if 0

machineObj = Machine()

##### Config - End #####



##### Serial Work #####
serialQueue = []
serialQueuePaused = False
serialQueueCurrentMax = 0
serialLastSerialRead = ''
serialLastSerialWrite = []
thread = None


def start_serial(ser):
    ser.port = port
    ser.baudrate = baud
    ser.timeout = timeout
    ser.open()
    time.sleep(4)  # Needs time to start up
    ser.flush()


# Loop that listens to the serial and runs onDataReceived with resutls
# Also include GRBL poling "?" every "poll_interval" second
def serial_port_listener(ser):
    global poll_interval

    lastPoleTime = int(round(time.time() * 1000)) + 6000
    while True:

        if not ser.isOpen():
            start_serial(ser)

        if ser.inWaiting > 0:
            data = ser.readline()
            onDataReceived(data)

        if poll_interval > 0 and int(round(time.time() * 1000)) > lastPoleTime + poll_interval:
            print "Sending ?"
            lastPoleTime = int(round(time.time() * 1000))
            ser.write("?")


def onDataReceived(data):
    processData(data)


def StartSerialListener():
    if serial_port.isOpen():
        serial_port.close()

    thread = threading.Thread(target=serial_port_listener, args=(serial_port,))
    thread.start()


##### Serial Work - End #####



def sendSerialRead(color, type, line):
    try:
        line = line.encode('ascii', 'replace').replace('\r', '').replace('\n', '')
        socketio.emit('serialRead',
                      {'line': '<span style="color: ' + color + ';">' + type + ': ' + line + '</span>' + "\n"},
                      namespace='/test')
    except:
        print "Error: SendSerialRead: " + color + ' - ' + type + ' - ' + line + ' - '
        print str(sys.exc_info())


def convertChars(data):
    data = data.replace('<', '&lt;')
    data = data.replace('>', '&gt;')
    data = data.replace('&', '&amp;')
    data = data.replace('"', '&quot;')
    data = data.replace('#', '&#035;')
    return data


def processData(data):
    global serialQueueCurrentMax
    global serialLastSerialRead
    global serialQueue
    global machineObj

    if data != "":
        # Handle status("?") results
        if str(data).find('<') == 0:
            machineObj.parseData(data)

            socketio.emit('machineStatus',
                          {'status': machineObj.status, 'mpos': [machineObj.mpos_x, machineObj.mpos_y, machineObj.mpos_z],
                           'wpos': [machineObj.wpos_x, machineObj.wpos_y, machineObj.wpos_z]}, namespace='/test')
            return

        if serialQueuePaused:
            return

        data = convertChars(data)

        if str(data).find('ok') == 0:
            sendSerialRead('green', 'RESP', data)

            # Run next in queue
            if len(serialQueue) > 0:
                sendQueue()

                # // remove first
                #sp[port].lastSerialWrite.shift();

        elif str(data).find('error') == 0:
            sendSerialRead('red', 'RESP', data)

            # Run next in queue
            if len(serialQueue) > 0:
                sendQueue()

                # // remove first
                #sp[port].lastSerialWrite.shift();
        else:
            sendSerialRead('grey', 'RESP', data)

        if len(serialQueue) == 0:
            serialQueueCurrentMax = 0

        socketio.emit('qStatus',
                      {'currentLength': len(serialQueue), 'currentMax': serialQueueCurrentMax},
                      namespace='/test')
        serialLastSerialRead = data


def sendQueue():
    global serialQueue
    if (len(serialQueue) > 0):
        lineToProcess = serialQueue.pop(0)

        # remove comments and trim
        line = lineToProcess.split(";")[0].rstrip().rstrip('\n').rstrip('\r')
        if line == "" or line == ";":
            sendQueue()
            return

        sendSerialRead('black', 'SEND', line)

        serial_port.write(line + "\n")

        # sp[port].lastSerialWrite.push(t);

        print line + "\n"


##### Flask #####

@app.route('/')
def index():
    return app.send_static_file('index.html')


@socketio.on('connect', namespace='/test')
def test_connect():
    print "WS:Connect"
    emit('ports', [{'comName': '/dev/ttyUSB0', 'manufacturer': 'undefined', 'pnpId': 'USB0'}])


@socketio.on('gcodeLine', namespace='/test')
def gcodeLine(data):
    global serialQueue
    print "WS:gcodeLine"

    # Split lines
    lines = str(data['line']).split('\n')

    # Add lines to the serial queue
    for line in lines:
        serialQueue.append(line)

    sendQueue()


@socketio.on('clearQ', namespace='/test')
def clearQueue(input):
    global serialQueue
    serialQueue = []
    emit('qStatus', {'currentLength': 0, 'currentMax': 0})


@socketio.on('pause', namespace='/test')
def pause(data):
    global serialQueuePaused

    print data
    if data:
        serialQueuePaused = True
    else:
        serialQueuePaused = False
        sendQueue()


@socketio.on('doReset', namespace='/test')
def doReset(data):
    serial_port.write("\030")

    global serialQueue
    global serialQueueCurrentMax
    global serialLastSerialWrite
    global serialLastSerialRead

    serialQueue = []
    serialQueueCurrentMax = 0
    serialLastSerialWrite = []
    serialLastSerialRead = ''

@socketio.on('paused', namespace='/test')
def doReset(data):
    if data:
        serial_port.write("~")
    else:
        serial_port.write("!")


##### Flask - End #####


if __name__ == '__main__':
    try:
        StartSerialListener()
        socketio.run(app, host='0.0.0.0')
    except:
        print "Error"
        serial_port.close()
        thread.stop()
