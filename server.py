from gevent import monkey

monkey.patch_all()

from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect

import sys
import lib.machine as machine
import config
import lib.serialConnection as sc


app = Flask(__name__, static_url_path='')
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


##### Config #####

serialConn = None

def pollingFunction(ser):
    print "Sending: ?"
    ser.write('?')

def dataProcessFunc(data):
    processData(data)



serialConn = sc.SerialConnection(config.serial_port, config.serial_baud, config.serial_timeout, dataProcessFunc, pollingFunction,
                                 config.position_poll_interval)



machineObj = machine.Machine()

##### Config - End #####


##### Serial Work #####
serialQueue = []
serialQueuePaused = False
serialQueueCurrentMax = 0
serialLastSerialRead = ''
serialLastSerialWrite = []
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
                          {'status': machineObj.status,
                           'mpos': [machineObj.mpos_x, machineObj.mpos_y, machineObj.mpos_z],
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

        serialConn.serial_send(line + "\n")

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
    serialConn.serial_send("\030")

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
        serialConn.serial_send("~")
    else:
        serialConn.serial_send("!")


##### Flask - End #####


if __name__ == '__main__':
    try:
        serialConn.StartSerialListener()
        socketio.run(app, host='0.0.0.0')
    except:
        print "Error"
        serialConn.StopSerialListener()
