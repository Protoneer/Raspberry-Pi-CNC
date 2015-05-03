from gevent import monkey

monkey.patch_all()

from flask import Flask
from flask.ext.socketio import SocketIO, emit, disconnect

import sys
import lib.machine as machine
import config
import lib.serialConnection as sc
import lib.commandProcessor as cp


app = Flask(__name__, static_url_path='')
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def webSocketEmit(MessageType,data):
    socketio.emit(MessageType,
              data,
              namespace='/test')



@app.route('/')
def index():
    return app.send_static_file('index.html')


@socketio.on('connect', namespace='/test')
def test_connect():
    print "WS:Connect"
    emit('ports', [{'comName': '/dev/ttyUSB0', 'manufacturer': 'undefined', 'pnpId': 'USB0'}])


@socketio.on('gcodeLine', namespace='/test')
def gcodeLine(data):
    print "WS:gcodeLine"

    # Split lines
    lines = str(data['line']).split('\n')

    # Add lines to the serial queue
    for line in lines:
        machineObj.Queue.append(line)

    cp.ProcessNextLineInQueue()


@socketio.on('clearQ', namespace='/test')
def clearQueue(input):
    machineObj.Queue = []
    emit('qStatus', {'currentLength': 0, 'currentMax': 0})


@socketio.on('pause', namespace='/test')
def pause(data):
    print data
    if data:
        machineObj.QueuePaused = True
    else:
        machineObj.QueuePaused = False
        cp.ProcessNextLineInQueue()


@socketio.on('doReset', namespace='/test')
def doReset(data):
    serialConn.serial_send("\030")

    machineObj.Queue = []
    machineObj.QueueCurrentMax = 0
    machineObj.LastSerialReadData = ''
    machineObj.LastSerialSendData = []


@socketio.on('paused', namespace='/test')
def doReset(data):
    if data:
        serialConn.serial_send("~")
    else:
        serialConn.serial_send("!")

@socketio.on('refreshSettings', namespace='/test')
def getSettings(data):
    machineObj.Settings = []
    machineObj.Queue.append("$$")
    cp.ProcessNextLineInQueue()

@socketio.on('machineSettings', namespace='/test')
def getSettings(data):
    emit('machineSettings', machineObj.Settings)


if __name__ == '__main__':
    serialConn = None
    try:
        machineObj = machine.Machine()

        serialConn = sc.SerialConnection(config.serial_port, config.serial_baud, config.serial_timeout, cp.processData,
                                         machineObj.pollingFunction, config.position_poll_interval)

        cp.init(machineObj, webSocketEmit, serialConn)

        serialConn.StartSerialListener()
        socketio.run(app, host='0.0.0.0')
    except:
        print "Error"
        serialConn.StopSerialListener()
