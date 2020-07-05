from mininet.topo import Topo
class homeworkTopo(Topo):
    def __init__(self):
        Topo.__init__(self)
#        c = self.addController('c')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
 #       self.addLink(s1,c)
        self.addLink(s1,s2)
        self.addLink(s2,s3)
        self.addLink(s2,s4)
        self.addLink(s2,s5)
        self.addLink(s3,h1)
        self.addLink(h2,s4)
        self.addLink(h3,s5)
        self.addLink(h4,s5)


class MyTopo(Topo):

    def __init__(self):
        super(MyTopo,self).__init__()

        # add host
        Host1 = self.addHost('h1')
        Host2 = self.addHost('h2')
        Host3 = self.addHost('h3')

        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')

        self.addLink(Host1,switch1)
        self.addLink(Host2,switch1)
        self.addLink(Host3,switch2)
        self.addLink(switch1,switch2)

class DataCenter(Topo):

    def __init__(self):
        super(DataCenter,self).__init__()

        #Marking the number of switch for per level
        L1 = 2;    
        L2 = L1*2
        L3 = L2

        #Starting create the switch
        c = []    #core switch
        a = []    #aggregate switch
        e = []    #edge switch

        #notice: switch label is a special data structure
        for i in range(L1):
            c_sw = self.addSwitch('c{}'.format(i+1))    #label from 1 to n,not start with 0
            c.append(c_sw)

        for i in range(L2):
            a_sw = self.addSwitch('a{}'.format(L1+i+1))
            a.append(a_sw)

        for i in range(L3):
            e_sw = self.addSwitch('e{}'.format(L1+L2+i+1))
            e.append(e_sw)

        #Starting create the link between switchs
        #first the first level and second level link
        for i in range(L1):
            c_sw = c[i]
            for j in range(L2):
                self.addLink(c_sw,a[j])

        #second the second level and third level link
        for i in range(L2):
            self.addLink(a[i],e[i])
            if not i%2:
                self.addLink(a[i],e[i+1])
            else:
                self.addLink(a[i],e[i-1])

        #Starting create the host and create link between switchs and hosts
        for i in range(L3):
            for j in range(2):
                hs = self.addHost('h{}'.format(i*2+j+1))
                self.addLink(e[i],hs)


topos = {'homeworkTopo':(lambda:homeworkTopo()),"mytopo":(lambda:MyTopo()),'datacenter':(lambda:DataCenter())}

# sudo mn --custom=homeworktopo.py --topo homeworkTopo
