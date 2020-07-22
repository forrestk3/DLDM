class FlowEntry:
    sIP = None
    dIP = None
    sPort = None
    dPort = None
    proto = None

    def __init__(self,sIP = None,dIP = None,sPort = None,dPort = None,proto = None):
        self.sIP = sIP
        self.dIP = dIP
        self.sPort = sPort
        self.dPort = dPort
        self.proto = proto

    def isSymFlow(self,flow):
        if flow.getSIP() == self.dIP and flow.getDIP() == self.sIP:
            return True
        return False

    def getSIP(self):
        return self.sIP

    def getDIP(self):
        return self.dIP
    def __eq__(self,other):
        if isinstance(other,self.__class__):
            return self.sIP == other.getSIP() and self.dIP == other.getDIP() and self.sPort == other.sPort and self.dPort == other.dPort and self.proto == other.proto
        else:
            return False

    def __hash__(self):
        hash_str = self.sIP + self.dIP + str(self.sPort) + str(self.dPort) + str(self.proto)
        return hash(hash_str)


if __name__ == '__main__':
    # print('oh yeah!!!')
    flow = FlowEntry(sIP='1',dIP='2', sPort=3, dPort=4, proto=5001)
    flow2 = FlowEntry(sIP='1',dIP='2', sPort=3, dPort=4, proto=5001)
    # print(flow.getDIP())
    print(flow.__eq__(flow2))
    my_set = set()
    my_set.add(flow2)
    my_set.add(flow)
    print(my_set,len(my_set))
