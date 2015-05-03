import sys
import re

machineObj = None
webSocketEmit = None
serialConn = None

def convertChars(data):
    data = data.replace('<', '&lt;')
    data = data.replace('>', '&gt;')
    data = data.replace('&', '&amp;')
    data = data.replace('"', '&quot;')
    data = data.replace('#', '&#035;')
    return data

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
        if not SetUP(data):
            return

        if IsOK(data):
            ForwardSerialDataToSubscribers('green', 'RESP', convertChars(data))

            # Run next in queue
            if len(machineObj.Queue) > 0:
                ProcessNextLineInQueue()
                machineObj.LastSerialSendData.pop()

        elif IsError(data):
            ForwardSerialDataToSubscribers('red', 'RESP', convertChars(data))

            # Run next in queue
            if len(machineObj.Queue) > 0:
                ProcessNextLineInQueue()
                machineObj.LastSerialSendData.pop()

        elif IsMachineSetting(data):
            UpdateMachineSettings(data)
            #SendMachineSettings()
            #ForwardSerialDataToSubscribers('blue', 'RESP', convertChars(data))
        else:
            ForwardSerialDataToSubscribers('grey', 'RESP', convertChars(data))

        TearDown(data)

def IsMachineSetting(data):
    return re.search("^\$\d+=.*\(.*\).*", data)

def IsError(data):
    return re.search("^error", data)

def IsOK(data):
    return re.search("^ok",data)

def IsStatusMessage(data):
    return re.search("^\<",data)

def UpdateMachineSettings(data):
    machineObj.Settings.append(data)


def SendMachineSettings():
    webSocketEmit('machineSettings',
                  {'status': machineObj.status,
                   'mpos': [machineObj.mpos_x, machineObj.mpos_y, machineObj.mpos_z],
                   'wpos': [machineObj.wpos_x, machineObj.wpos_y, machineObj.wpos_z]})


def SetUP(data):
    # Handle status("?") results
    if IsStatusMessage(data):
        machineObj.parseData(data)
        webSocketEmit('machineStatus',
                      {'status': machineObj.status,
                       'mpos': [machineObj.mpos_x, machineObj.mpos_y, machineObj.mpos_z],
                       'wpos': [machineObj.wpos_x, machineObj.wpos_y, machineObj.wpos_z]})
        return False
    if machineObj.QueuePaused:
        return False
    return True

def TearDown(data):
    if len(machineObj.Queue) == 0:
        machineObj.QueueCurrentMax = 0
    webSocketEmit('qStatus',
                  {'currentLength': len(machineObj.Queue), 'currentMax': machineObj.QueueCurrentMax})
    machineObj.LastSerialReadData = data

def ProcessNextLineInQueue():
    if (len(machineObj.Queue) > 0):
        lineToProcess = machineObj.Queue.pop(0)

        # remove comments and trim
        line = lineToProcess.split(";")[0].rstrip().rstrip('\n').rstrip('\r')
        if line == "" or line == ";":
            ProcessNextLineInQueue()
            return

        ForwardSerialDataToSubscribers('black', 'SEND', line)

        serialConn.serial_send(line + "\n")

        machineObj.LastSerialSendData.append(line)

        print line + "\n"

def ForwardSerialDataToSubscribers(color, type, line):
    try:
        line = line.encode('ascii', 'replace').replace('\r', '').replace('\n', '')
        webSocketEmit('serialRead',
                      {'line': '<span style="color: ' + color + ';">' + type + ': ' + line + '</span>' + "\n"})
    except:
        print "Error: SendSerialRead: " + color + ' - ' + type + ' - ' + line + ' - '
        print str(sys.exc_info())
