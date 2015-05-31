import sys
import re
import time

machineObj = None
webSocketEmit = None
serialConn = None

# In singleCommandMode sending commands need to be slowed down allowing machine to go into run mode before sending next
lastPoleTime = None


def convertChars(data):
    data = data.replace('<', '&lt;')
    data = data.replace('>', '&gt;')
    data = data.replace('&', '&amp;')
    data = data.replace('"', '&quot;')
    data = data.replace('#', '&#035;')
    return data


def init(mac, wsEmit, serialConnection):
    global machineObj
    global webSocketEmit
    global serialConn

    machineObj = mac
    webSocketEmit = wsEmit
    serialConn = serialConnection
    resetPollingTime()


# Processes Commands one line at a time
def processData(data):
    if data != "":
        global lastPoleTime

        # Check for Machine Status message
        if IsStatusMessage(data):
            machineObj.parseData(data)
            webSocketEmit('machineStatus',
                          {'status': machineObj.status,
                           'mpos': [machineObj.mpos_x, machineObj.mpos_y, machineObj.mpos_z],
                           'wpos': [machineObj.wpos_x, machineObj.wpos_y, machineObj.wpos_z]})

            return

        # Process data
        if IsOK(data):
            ForwardSerialDataToSubscribers('green', 'RESP', convertChars(data))
            IfStreamingModeSendNextCommand()
        elif IsError(data):
            ForwardSerialDataToSubscribers('red', 'RESP', convertChars(data))
            IfStreamingModeSendNextCommand()
        elif IsMachineSetting(data):
            UpdateMachineSettings(data)
        else:
            ForwardSerialDataToSubscribers('grey', 'RESP', convertChars(data))

        # Clean up
        if len(machineObj.Queue) == 0:
            machineObj.QueueCurrentMax = 0

        webSocketEmit('qStatus',
                      {'currentLength': len(machineObj.Queue), 'currentMax': machineObj.QueueCurrentMax})

        machineObj.LastSerialReadData = data

def IfStreamingModeSendNextCommand():
    if not machineObj.SingleCommandMode:
        ProcessNextLineInQueue()

def IsMachineSetting(data):
    return re.search("^\$\d+=.*\(.*\).*", data)


def IsError(data):
    return re.search("^error", data)


def IsOK(data):
    return re.search("^ok", data)


def IsStatusMessage(data):
    return re.search("^\<", data)


def UpdateMachineSettings(data):
    machineObj.Settings.append(data)

def resetPollingTime():
    global lastPoleTime
    lastPoleTime = int(round(time.time() * 1000)) + 250 + 500 # 250 is the polling time




def ProcessNextLineInQueue():
    if len(machineObj.Queue) > 0 and not machineObj.QueuePaused:
        line = machineObj.Queue.pop(0).split(";")[0].rstrip().rstrip('\n').rstrip('\r')

        ForwardSerialDataToSubscribers('black', 'SEND', line)

        commandRouting(line)

        print line + "\n"

def commandRouting(line):

    # Skip empty and comment lines
    if line == "" or line == ";":
        return


    if line == "RUNPYTHON":
        SendRunPythonCommand(line)
    else:
        SendSerialCommand(line)


def SendSerialCommand(line):
    serialConn.serial_send(line + "\n")


def SendRunPythonCommand(line):
    import subprocess

    subprocess.call(['ping', '-c', '3', '127.0.0.1'])
    print "PYTHON ROCKS!!!"
    ProcessNextLineInQueue()

def ForwardSerialDataToSubscribers(color, type, line):
    try:
        line = line.encode('ascii', 'replace').replace('\r', '').replace('\n', '')
        webSocketEmit('serialRead',
                      {'line': '<span style="color: ' + color + ';">' + type + ': ' + line + '</span>' + "\n"})
    except:
        print "Error: SendSerialRead: " + color + ' - ' + type + ' - ' + line + ' - '
        print str(sys.exc_info())


def queuePollingFunction(interval):
    import threading
    print "CheckingQueue"
    if (len(machineObj.Queue) > 0) and not machineObj.QueuePaused:
        if machineObj.SingleCommandMode:
            if machineObj.status == 'Idle' and int(round(time.time() * 1000)) > lastPoleTime:
                ProcessNextLineInQueue()
                resetPollingTime()
        #else:
        #    ProcessNextLineInQueue()

    thread = threading.Timer(interval, queuePollingFunction, args=[interval])
    thread.daemon = True
    thread.start()