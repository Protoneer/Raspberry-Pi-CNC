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




##### Config #####

port = '/dev/ttyUSB0'
baud = 9600
timeout = 1
serial_port = serial.Serial(port, baud, timeout=timeout)
poll_interval = 1  # Disabled if 0

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

    lastPoleTime = datetime.datetime.now() + datetime.timedelta(seconds=6)
    while True:
        if (ser.isOpen() == False):
            start_serial(ser)

        if ser.inWaiting > 0:
            data = ser.readline()
            onDataReceived(data)

        if poll_interval != 0 and datetime.datetime.now() > lastPoleTime + datetime.timedelta(seconds=poll_interval):
            print "Sending ?"
            lastPoleTime = datetime.datetime.now()
            ser.write("?")

def onDataReceived(data):
    processData(data)

def StartSerialListener():
    thread = threading.Thread(target=serial_port_listener, args=(serial_port,))
    thread.start()

##### Serial Work - End #####



def sendSerialRead(color,type,line):
    try:
        line = line.replace('\r','').replace('\n','')
        socketio.emit('serialRead',
                      {'line':'<span style="color: '+color+';">'+type+': '+ line +'</span>'+"\n"},
                      namespace='/test')
    except:
        print "Error: SendSerialRead: " +color + ' - ' + type + ' - ' + line + ' - '
        print sys.exc_info()[0]

def convertChars(data):
    data = data.replace('<', '&lt;')
    data = data.replace('>', '&gt;')
    data = data.replace('&', '&amp;')
    data = data.replace('"', '&quot;')
    data = data.replace("'", '&#039;')
    data = data.replace('#', '&#035;')
    return data




def processData(data):
    global serialQueueCurrentMax
    global serialLastSerialRead
    global serialQueue

    if data != "":
        # Handle status("?") results
        if str(data).find('<') == 0:
            positions = str(data).replace("<", "").replace(">", "").replace("MPos:", "").replace("WPos:", "").replace(
                "\r\n", "").split(",")
            socketio.emit('machineStatus',
                          {'status': positions[0], 'mpos': [positions[1], positions[2], positions[3]],
                           'wpos': [positions[4], positions[5], positions[6]]}, namespace='/test')
            return

        if serialQueuePaused:
            return

        data = convertChars(data)

        if str(data).find('ok') == 0:
            sendSerialRead('green','RESP', data)

            # Run next in queue
            if len(serialQueue) > 0:
                sendQueue()

            #// remove first
            #sp[port].lastSerialWrite.shift();

        elif str(data).find('error') == 0:
            sendSerialRead('red','RESP', data)

            # Run next in queue
            if len(serialQueue) > 0:
                sendQueue()

            #// remove first
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
    if(len(serialQueue) > 0):
        lineToProcess = serialQueue.pop(0)

        # remove comments and trim
        line = lineToProcess.split(";")[0].rstrip().rstrip('\n').rstrip('\r')
        if line == "" or line == ";":
            sendQueue()
            return

        sendSerialRead('black','SEND', line)

        serial_port.write(line+"\n")

        #sp[port].lastSerialWrite.push(t);

        print line + "\n"





##### Flask #####

@app.route('/')
def index():
    return render_template('index.html')


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



##### Flask - End #####


if __name__ == '__main__':
    try:
        StartSerialListener()
        socketio.run(app, host='0.0.0.0')
    except:
        print "Error"
        thread.stop()
        serial_port.close()