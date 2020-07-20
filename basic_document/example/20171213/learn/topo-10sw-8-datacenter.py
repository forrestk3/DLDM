"""Custom topology example

  2sw

  4sw

  4sw

  8host
"""
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
net=Mininet(host=CPULimitedHost,link=TCLink)
#creating nodes in the network


c0=net.addController(name='c0', controller=RemoteController, ip='127.0.0.1', port=6633 )
s1 = net.addSwitch( 's1', dpid='0000000000000001', protocols=["OpenFlow13"])
s2 = net.addSwitch( 's2', dpid='0000000000000002', protocols=["OpenFlow13"])
s3 = net.addSwitch( 's3', dpid='0000000000000003', protocols=["OpenFlow13"])
s4 = net.addSwitch( 's4', dpid='0000000000000004', protocols=["OpenFlow13"])
s5 = net.addSwitch( 's5', dpid='0000000000000005', protocols=["OpenFlow13"])
s6 = net.addSwitch( 's6', dpid='0000000000000006', protocols=["OpenFlow13"])
s7 = net.addSwitch( 's7', dpid='0000000000000007', protocols=["OpenFlow13"])
s8 = net.addSwitch( 's8', dpid='0000000000000008', protocols=["OpenFlow13"])
s9 = net.addSwitch( 's9', dpid='0000000000000009', protocols=["OpenFlow13"])
s10 = net.addSwitch( 's10', dpid='000000000000000A', protocols=["OpenFlow13"])
#add hosts
h1 = net.addHost( 'h1',mac='00:00:00:00:00:01')
h2 = net.addHost( 'h2',mac='00:00:00:00:00:02')
h3 = net.addHost( 'h3',mac='00:00:00:00:00:03')
h4 = net.addHost( 'h4',mac='00:00:00:00:00:04')
h5 = net.addHost( 'h5',mac='00:00:00:00:00:05')
h6 = net.addHost( 'h6',mac='00:00:00:00:00:06')
h7 = net.addHost( 'h7',mac='00:00:00:00:00:07')
h8 = net.addHost( 'h8',mac='00:00:00:00:00:08')

#Creating links between nodes in network
#bw=1  1Mbps=1000kbps
#net.addLink(s0,h0,port1=None,port2=None,bw=10,delay='5ms',max_queue_size=100,loss=10,use_htb=True)
net.addLink( s1, h1, 1 )
net.addLink( s1, h2, 2 )
net.addLink( s2, h3, 1 )
net.addLink( s2, h4, 2 )
net.addLink( s3, h5, 1 )
net.addLink( s3, h6, 2 )
net.addLink( s4, h7, 1 )
net.addLink( s4, h8, 2 )

net.addLink( s1, s5, 3, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s1, s6, 4, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s1, s7, 5, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s1, s8, 6, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)

net.addLink( s2, s5, 3, 2 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s2, s6, 4, 2 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s2, s7, 5, 2 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s2, s8, 6, 2 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)

net.addLink( s3, s5, 3, 3 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s3, s6, 4, 3 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s3, s7, 5, 3 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s3, s8, 6, 3 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)

net.addLink( s4, s5, 3, 4 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s4, s6, 4, 4 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s4, s7, 5, 4 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s4, s8, 6, 4 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)

net.addLink( s9, s5, 1, 5 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s9, s6, 2, 5 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s9, s7, 3, 5 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s9, s8, 4, 5 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)

net.addLink( s10, s5, 1, 6 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s10, s6, 2, 6 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s10, s7, 3, 6 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s10, s8, 4, 6 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)

net.start()
#net.pingAll()
#add qos
'''
s2_htb_QoS='sudo ovs-vsctl set port s2-eth5 qos=@newqos -- \
	--id=@newqos create qos type=linux-htb other-config:max-rate=8000000 queues=0=@q0,1=@q1,2=@q2,3=@q3 -- \
	--id=@q0 create queue other-config:min-rate=1600000 other-config:max-rate=1600000 other-config:priority=1 -- \
	--id=@q1 create queue other-config:min-rate=1000 other-config:max-rate=6400000 other-config:priority=2 -- \
	--id=@q2 create queue other-config:min-rate=1000 other-config:max-rate=6400000 other-config:priority=3 -- \
	--id=@q3 create queue other-config:min-rate=1000 other-config:max-rate=6400000 other-config:priority=4'
s2.cmd(s2_htb_QoS)
'''
'''
sws=['s1','s2','s3','s4','s5','s6','s7']
for sw in sws:
	s=net.getNodeByName(sw)
	s.cmd('ovs-vsctl set bridge '+sw+' protocols=OpenFlow13')
'''
CLI(net)
'''
s2.cmd('ovs-vsctl clear Port s2-eth5 qos')
s2.cmd('ovs-vsctl --all destroy qos')
s2.cmd('ovs-vsctl --all destroy queue')
print 'clear qos an queue'
'''
net.stop()