from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib import hub
from ryu.topology.api import get_all_host, get_all_link, get_all_switch
from ryu.lib.packet import arp
from ryu.lib.packet import icmp
from ryu.lib.packet import ether_types
from ryu.lib import mac
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches
import networkx as nx

ETHERNET = ethernet.ethernet.__name__
ETHERNET_MULTICAST = "ff:ff:ff:ff:ff:ff"
ARP = arp.arp.__name__

class NetworkAwareness(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(NetworkAwareness, self).__init__(*args, **kwargs)
        self.mac_table = {} #dpid,dst:port,由交换机的id和主机的物理地址找到交换机对应的port
        self.arp_table = {} #IP:MAC
        self.topo_thread = hub.spawn(self._get_topology)
        self.graph = nx.DiGraph()
        self.topology_api_app = self
        self.switch_host_port = {}   #每个键为dpid,其对应值为所有与主机连接的端口
        self.datapath_switch = {} #保存每个switch,dpid:dp


    @set_ev_cls(ofp_event.EventOFPPacketIn,MAIN_DISPATCHER)
    def packet_in_handler(self,ev):
        # 下面是一些套路
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        pkt = packet.Packet(msg.data)
        dpid = dp.id
        in_port = msg.match['in_port']
        self.logger.info("packet_in %s %s %s %s",dpid,src,dst,in_port)
        # 获取一些基本信息
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src
        # 向switch集中添加没有的dp,并忽略LLDP和IPV6包.
        if not self.datapath_switch.get(dpid):
            self.datapath_switch[dpid] = dp
        if eth_pkt.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        if eth_pkt.ethertype == ether_types.ETH_TYPE_IPV6:
            return

        header_list = dict((p.protocol_name,p) for p in pkt.protocols if type(p) != str)
        # 若包类型是ARP且目的物理地址广播,则处理:目的地址没找到则发给所有主机;找到则交给stp处理
        if dst == ETHERNET_MULTICAST and ARP in header_list:
            # 先将源IP与其对应的物理地址保存
            self.arp_table[header_list[ARP].src_ip] = src
            arp_dst_ip = header_list[ARP].dst_ip
            print("received packet_in,%s send arp to %s"%(header_list[ARP].src_ip,header_list[ARP].dst_ip))
            if not self.arp_table.get(arp_dst_ip):
                #若目的IP没有保存过,则向所有与主机连接的端口发送
                for key in self.switch_host_port:
                    if key != dpid:
                        dp = self.datapath_switch[key]
                        for out_port in self.switch_host_port[key]:
                            out = parser.OFPPacketOut(datapath = dp,
                                                      buffer_id = ofp.OFP_NO_BUFFER,
                                                      in_port = ofp.OFPP_CONTROLLER,
                                                      actions=[parser.OFPActionOutput(out_port)],
                                                      data = msg.data)
                            print('send packetout to dpid:%s,port:%s'%(key,out_port))
                            dp.send_msg(out)
                        print()
            else:
                #保存过则直接找即可得,此时src为源主机的物理地址,dst为目的主机的物理地址
                #剩下的交给最短路径处理 
                dst = self.arp_table[arp_dst_ip]


        self.mac_table.setdefault(dpid,{})
        # 规定当前交换机如何处理该目的dst:若控制器已存储则获取,未存储则洪泛
        if self.mac_table[dpid].get(dst): 
            out_port = self.mac_table[dpid][dst]
        else:
            out_port = ofp.OFPP_FLOOD

        # 将当前的发送主机加入拓扑图中
        if src not in self.graph:
            self.graph.add_node(src)
            self.graph.add_edge(dpid,src,weight=0,port=in_port)
            self.graph.add_edge(src,dpid,weight=0)
        # 若源,目的,当前的dp都在拓扑中,则可通过最知路径算法找最知路径
        if src in self.graph and dst in self.graph and dpid in self.graph:
            path = nx.shortest_path(self.graph,src,dst,weight='weight')
            #若当前dp不在最短路径上则丢弃该包即可(这里控制器不作处理,没有buffer,则跟丢弃一样)
            if dpid not in path:
                return
            # 若当前dp在最短路径上,则通过获得的path拿到当前dp要交付的out_port,并发送
            # 覆盖前面的mac_table的out_port
            nxt = path[path.index(dpid)+1]
            out_port = self.graph[dpid][nxt]['port']
            self.mac_table[dpid][dst]=out_port
            actions = [parser.OFPActionOutput(out_port)]
            out = parser.OFPPacketOut(datapath=dp,
                                      buffer_id=ofp.OFP_NO_BUFFER,
                                      in_port=in_port,
                                      actions=actions,
                                      data=msg.data)
            dp.send_msg(out)

        # 若这三个节点有不在拓扑中的就按mac_table的端口结果转发
        else:
            actions = [parser.OFPActionOutput(out_port)]
            out = parser.OFPPacketOut(datapath = dp,
                                      buffer_id = ofp.OFP_NO_BUFFER,
                                      in_port = in_port,
                                      actions = actions,
                                      data = msg.data)
            dp.send_msg(out)

    def add_flow(self,datapath,priority,match,actions):
        dp = datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,actions)]
        mod=parser.OFPFlowMod(datapath=dp,
                              priority=priority,
                              match=match,
                              instructions=inst)
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,CONFIG_DISPATCHER)
    def switch_features_handler(self,ev):
        msg = ev.msg
        dp = msg.datapath
        self.datapath_switch[dp.id]=dp
        print("add dp:%s"%(dp.id))
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER,ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp,0,match,actions)
        
    # 该函数应该定期执行的,这里只执行一次
    def _get_topology(self):
        hub.sleep(2)
        # 通过获取node和link,并将结果加入networkx的graph中构建网络拓扑
        switch_list=get_switch(self.topology_api_app,None)
        switches = [switch.dp.id for switch in switch_list]
        self.graph.add_nodes_from(switches)

        link_list = get_link(self.topology_api_app,None)
        for link in link_list:
            self.graph.add_edge(link.src.dpid,link.dst.dpid,
                                weight=1,port=link.src.port_no)
            self.graph.add_edge(link.dst.dpid,link.src.dpid,
                                weight=1,port=link.dst.port_no)

        # 获得所有与主机连接的交换机的端口
        switch_all_port = {}
        for switch in switch_list:
            dpid = switch.dp.id
            # 1.获得所有的交换机及其端口
            flag = False
            for port in switch.ports:
                if flag:
                    switch_all_port[dpid].add(port.port_no)
                    continue
                if not switch_all_port.get(dpid):
                    switch_all_port[dpid] = {port.port_no}
                    flag = True

            # 2.在前面的基础上删掉所有交换机之间的端口            
            for link in link_list:
                link_src = link.src
                link_dst = link.dst
                if switch_all_port.get(link_src.dpid):
                    switch_all_port[link_src.dpid].discard(link_src.port_no)
                if switch_all_port.get(link_dst.dpid):
                    switch_all_port[link_dst.dpid].discard(link_dst.port_no)
        self.switch_host_port = switch_all_port
        
        print("nodes:",end='')
        print(self.graph.nodes())
        print("links:",end='')
        print(self.graph.edges())
        print("swithc_host_port:",end='')
        print(self.switch_host_port)
        
            
