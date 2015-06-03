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
              data)



@app.route('/')
def index():
    return app.send_static_file('index.html')

@socketio.on('command')
def command(data):
    if data['cmd'] == 'singleCommandMode':
        machineObj.SingleCommandMode = data['value']
        emit('singleCommandMode', machineObj.SingleCommandMode)
        cp.IfStreamingModeSendNextCommand() # Restart Stream mode if needed
    elif data['cmd'] == 'doReset':
        serialConn.serial_send("\030")
        machineObj.Queue = []
        machineObj.QueueCurrentMax = 0
        machineObj.LastSerialReadData = ''
    elif data['cmd'] == 'gcodeLine':
        print "WS:gcodeLine"
        # Split lines
        lines = str(data['line']).split('\n')

        # Streaming mode need to be started once the queue is empty.
        # SingleLineMode polls and does not need this.
        needToStartStreamingQueue = True if len(machineObj.Queue) == 0 else False

        # Add lines to the serial queue
        for line in lines:
            machineObj.Queue.append(line)

        if needToStartStreamingQueue:
            cp.IfStreamingModeSendNextCommand()
    elif data['cmd'] == 'paused':
        print data['value']
        if data['value']:
            serialConn.serial_send("!")
        else:
            serialConn.serial_send("~")
    elif data['cmd'] == 'pause':
        if data['value']:
            machineObj.QueuePaused = True
            print machineObj.QueuePaused
        else:
            machineObj.QueuePaused = False
            print machineObj.QueuePaused
            cp.IfStreamingModeSendNextCommand()
    elif data['cmd'] == 'clearQ':
        machineObj.Queue = []
        emit('qStatus', {'currentLength': 0, 'currentMax': 0})
    elif data['cmd'] == 'refreshSettings':
        machineObj.Settings = []
        cp.commandRouting("$$")
    elif data['cmd'] == 'machineSettings':
        emit('singleCommandMode', machineObj.SingleCommandMode)
        emit('machineSettings', machineObj.Settings)
    '''
    elif data['cmd'] in ['spnCW', 'spnCCW', 'spn']:
        print "spn"
    elif data['cmd'] == 'cool':
        print "cool"
    '''


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
    socketio.run(app, host='0.0.0.0', port=8081)


