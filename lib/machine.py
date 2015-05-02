class Machine:
    status = ''
    mpos_x = 0
    mpos_y = 0
    mpos_z = 0
    wpos_x = 0
    wpos_y = 0
    wpos_z = 0

    QueuePaused = False
    Queue = []
    QueueCurrentMax = 0
    LastSerialReadData = ''
    LastSerialSendData = []


    def parseData(self, data):
        fields = str(data).replace("<", "").replace(">", "").replace("MPos:", "").replace("WPos:", "") \
            .replace("\r\n", "").split(",")

        self.status = fields[0]
        self.mpos_x = fields[1]
        self.mpos_y = fields[2]
        self.mpos_z = fields[3]
        self.wpos_x = fields[4]
        self.wpos_y = fields[5]
        self.wpos_z = fields[6]

    def pollingFunction(self, ser):
        print "Sending: ?"
        ser.write('?')
