import sys

def convertChars(data):
    data = data.replace('<', '&lt;')
    data = data.replace('>', '&gt;')
    data = data.replace('&', '&amp;')
    data = data.replace('"', '&quot;')
    data = data.replace('#', '&#035;')
    return data

machineObj = None
webSocketEmit = None
serialConn = None

def init(mac,wsEmit,serialConnection):
    global machineObj
    global webSocketEmit
    global serialConn

    machineObj = mac
    webSocketEmit = wsEmit
    serialConn = serialConnection

# Processes Commands one line at a time
def processData(data):
    if data != "":
        # Handle status("?") results
        if str(data).find('<') == 0:
            machineObj.parseData(data)

            webSocketEmit('machineStatus',
                          {'status': machineObj.status,
                           'mpos': [machineObj.mpos_x, machineObj.mpos_y, machineObj.mpos_z],
                           'wpos': [machineObj.wpos_x, machineObj.wpos_y, machineObj.wpos_z]})
            '''
            socketio.emit('machineStatus',
                          {'status': machineObj.status,
                           'mpos': [machineObj.mpos_x, machineObj.mpos_y, machineObj.mpos_z],
                           'wpos': [machineObj.wpos_x, machineObj.wpos_y, machineObj.wpos_z]}, namespace='/test')
            '''
            return

        if machineObj.QueuePaused:
            return

        data = convertChars(data)

        if str(data).find('ok') == 0:
            sendSerialRead('green', 'RESP', data)

            # Run next in queue
            if len(machineObj.Queue) > 0:
                sendQueue()
                machineObj.LastSerialSendData.pop()

        elif str(data).find('error') == 0:
            sendSerialRead('red', 'RESP', data)

            # Run next in queue
            if len(machineObj.Queue) > 0:
                sendQueue()
                machineObj.LastSerialSendData.pop()
        else:
            sendSerialRead('grey', 'RESP', data)

        if len(machineObj.Queue) == 0:
            machineObj.QueueCurrentMax = 0

        webSocketEmit('qStatus',
                      {'currentLength': len(machineObj.Queue), 'currentMax': machineObj.QueueCurrentMax})

        '''
        socketio.emit('qStatus',
                      {'currentLength': len(machineObj.Queue), 'currentMax': machineObj.QueueCurrentMax},
                      namespace='/test')
        '''

        machineObj.LastSerialReadData = data


def sendQueue():
    if (len(machineObj.Queue) > 0):
        lineToProcess =  machineObj.Queue.pop(0)

        # remove comments and trim
        line = lineToProcess.split(";")[0].rstrip().rstrip('\n').rstrip('\r')
        if line == "" or line == ";":
            sendQueue()
            return

        sendSerialRead('black', 'SEND', line)

        serialConn.serial_send(line + "\n")

        machineObj.LastSerialSendData.append(line)

        print line + "\n"

def sendSerialRead(color, type, line):
    try:
        line = line.encode('ascii', 'replace').replace('\r', '').replace('\n', '')
        webSocketEmit('serialRead',
                      {'line': '<span style="color: ' + color + ';">' + type + ': ' + line + '</span>' + "\n"})
        '''
        socketio.emit('serialRead',
                      {'line': '<span style="color: ' + color + ';">' + type + ': ' + line + '</span>' + "\n"},
                      namespace='/test')
        '''
    except:
        print "Error: SendSerialRead: " + color + ' - ' + type + ' - ' + line + ' - '
        print str(sys.exc_info())
