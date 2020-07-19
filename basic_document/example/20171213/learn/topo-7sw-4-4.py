"""Custom topology example

   4host --- 7switchs --- 4host


   					s2----s5
				   / |	 / |	
   h1------|	  /	 |	/  |	|------h5
		   |	 /   | /   |	|
   h2------|	/  	 |/	   |	|------h6
		   |---s1---s3-----s7---|
   h3------|	\	 |	   |	|------h7
		   |	 \	 |	   |	|
   h4------|	  \	 |	   |	|------h8
   				   \ |	   |
					s4-----s6
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
#add hosts
h1 = net.addHost( 'h1',cpu=0.5/5,mac='00:00:00:00:00:01')
h2 = net.addHost( 'h2',cpu=0.5/5,mac='00:00:00:00:00:02')
h3 = net.addHost( 'h3',cpu=0.5/5,mac='00:00:00:00:00:03')
h4 = net.addHost( 'h4',cpu=0.5/5,mac='00:00:00:00:00:04')
h5 = net.addHost( 'h5',cpu=0.5/5,mac='00:00:00:00:00:05')
h6 = net.addHost( 'h6',cpu=0.5/5,mac='00:00:00:00:00:06')
h7 = net.addHost( 'h7',cpu=0.5/5,mac='00:00:00:00:00:07')
h8 = net.addHost( 'h8',cpu=0.5/5,mac='00:00:00:00:00:08')
#Creating links between nodes in network
#bw=1  1Mbps=1000kbps
#net.addLink(s0,h0,port1=None,port2=None,bw=10,delay='5ms',max_queue_size=100,loss=10,use_htb=True)
net.addLink( s1, h1, 1 )
net.addLink( s1, h2, 2 )
net.addLink( s1, h3, 3 )
net.addLink( s1, h4, 4 )
net.addLink( s7, h5, 1 )
net.addLink( s7, h6, 2 )
net.addLink( s7, h7, 3 )
net.addLink( s7, h8, 4 )
net.addLink( s1, s2, 5, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s1, s3, 6, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s1, s4, 7, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s2, s5, 3, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s5, s7, 3, 5 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s4, s6, 3, 1 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s6, s7, 2, 7 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s3, s2, 2, 2 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s3, s4, 5, 2 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s3, s5, 3, 2 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
net.addLink( s3, s7, 4, 6 ,bw=1,delay='2ms',max_queue_size=100,loss=0,use_htb=True)
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
