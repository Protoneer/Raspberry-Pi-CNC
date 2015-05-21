from gevent import monkey

monkey.patch_all()

from flask import Flask
from flask.ext.socketio import SocketIO, emit
import lib.machine as machine
import config
import lib.serialConnection as sc
import lib.commandProcessor as cp
import threading
import sys


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

@socketio.on('command', namespace='/test')
def command(data):
    if data['cmd'] == 'singleCommandMode':
        machineObj.SingleCommandMode = data['cmd']
    elif data['cmd'] == 'doReset':
        serialConn.serial_send("\030")
        machineObj.Queue = []
        machineObj.QueueCurrentMax = 0
        machineObj.LastSerialReadData = ''
    elif data['cmd'] == 'gcodeLine':
        print "WS:gcodeLine"
        # Split lines
        lines = str(data['line']).split('\n')
        # Add lines to the serial queue
        for line in lines:
            machineObj.Queue.append(line)
    elif data['cmd'] == 'paused':
        print data['value']
        if data['value']:
            serialConn.serial_send("~")
        else:
            serialConn.serial_send("!")
    elif data['cmd'] == 'pause':
        print data
        if data:
            machineObj.QueuePaused = True
        else:
            machineObj.QueuePaused = False
    elif data['cmd'] == 'clearQ':
        machineObj.Queue = []
        emit('qStatus', {'currentLength': 0, 'currentMax': 0})
    elif data['cmd'] == 'refreshSettings':
        machineObj.Settings = []
        machineObj.Queue.append("$$")
    elif data['cmd'] == 'machineSettings':
        emit('machineSettings', machineObj.Settings)

if __name__ == '__main__':
    serialConn = None

    machineObj = machine.Machine()

    serialConn = sc.SerialConnection(config.serial_port, config.serial_baud, config.serial_timeout)
    cp.init(machineObj, webSocketEmit, serialConn)
    serialConn.StartSerialListener(cp.processData)

    # Start Machine Status Polling
    machineObj.pollingFunction(serialConn.serial_port, 0.25)

    # Start
    cp.queuePollingFunction(0.25)

    # Start Socket.IO
    socketio.run(app, host='0.0.0.0')


