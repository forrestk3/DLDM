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

        self.mac_table = {}

        self.arp_table = {}

        self.topo_thread = hub.spawn(self._get_topology)

        self.graph = nx.DiGraph()

        self.topology_api_app = self

        self.switch_host_port = {}        

        self.datapath_switch = {}

    def add_flow(self, datapath, priority, match, actions):

        dp = datapath

        ofp = dp.ofproto

        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(datapath=dp, priority=priority, match=match, instructions=inst)

        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)

    def switch_features_handler(self, ev):

        msg = ev.msg

        dp = msg.datapath

        ofp = dp.ofproto

        parser = dp.ofproto_parser

        match = parser.OFPMatch()

        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]

        self.add_flow(dp, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)

    def packet_in_handler(self, ev):

        msg = ev.msg

        dp = msg.datapath

        ofp = dp.ofproto

        parser = dp.ofproto_parser

        pkt = packet.Packet(msg.data)

        dpid = dp.id

        in_port = msg.match['in_port']      

        eth_pkt = pkt.get_protocol(ethernet.ethernet)

        dst = eth_pkt.dst

        src = eth_pkt.src

        if not self.datapath_switch.get(dpid):

            self.datapath_switch[dpid] = dp

        if eth_pkt.ethertype == ether_types.ETH_TYPE_LLDP:

            return

        if eth_pkt.ethertype == ether_types.ETH_TYPE_IPV6:

            return

        header_list = dict((p.protocol_name, p) for p in pkt.protocols if type(p) != str)

        if dst == ETHERNET_MULTICAST and ARP in header_list:

            self.arp_table[header_list[ARP].src_ip] = src

            arp_dst_ip = header_list[ARP].dst_ip

            if not self.arp_table.get(arp_dst_ip):

                for key in self.switch_host_port:

                    if key != dpid:

                        dp = self.datapath_switch[key]

                        for out_port in self.switch_host_port[key]:

                            out = parser.OFPPacketOut(

                                datapath=dp,

                                buffer_id=ofp.OFP_NO_BUFFER,

                                in_port=ofp.OFPP_CONTROLLER,

                                actions=[parser.OFPActionOutput(out_port)], data=msg.data)

                            dp.send_msg(out)

            else:

                dst = self.arp_table[arp_dst_ip]

        self.mac_table.setdefault(dpid, {})

        if self.mac_table[dpid].get(dst):

            out_port = self.mac_table[dpid][dst]

        else:

            out_port = ofp.OFPP_FLOOD

        if src not in self.graph:

            self.graph.add_node(src)

            self.graph.add_edge(dpid, src, weight=0, port=in_port)

            self.graph.add_edge(src, dpid, weight=0)

        if src in self.graph and dst in self.graph and dpid in self.graph:

            path = nx.shortest_path(self.graph, src, dst, weight="weight")

            if dpid not in path:

                return

            nxt = path[path.index(dpid) + 1]

            out_port = self.graph[dpid][nxt]['port']

            self.mac_table[dpid][dst] = out_port

            actions = [parser.OFPActionOutput(out_port)]

            out = parser.OFPPacketOut(

                datapath=dp, buffer_id=ofp.OFP_NO_BUFFER, in_port=in_port, actions=actions, data=msg.data)

            dp.send_msg(out)

            if nxt == dst and dpid == path[-2]:

                print("path:",src,"->",dst,end='')

                print("the length of the path {}".format(len(path)),end='')

                print(path[0],"->",end='')

                for item in path[1:-1]:

                    index = path.index(item)

                    print("{}:{}:{}".format(self.graph[item][path[index - 1]]['port'],item,self.graph[item][path[index + 1]]['port']),end='')

                    print("->",end='')

                print(path[-1],end='')

                print()

                return

        else:

            actions = [parser.OFPActionOutput(out_port)]

            out = parser.OFPPacketOut(

                datapath=dp, buffer_id=ofp.OFP_NO_BUFFER, in_port=in_port, actions=actions, data=msg.data)

            dp.send_msg(out)

    def _get_topology(self):

        hub.sleep(2)

        switch_list = get_switch(self.topology_api_app, None)

        switches = [switch.dp.id for switch in switch_list]

        self.graph.add_nodes_from(switches)

        link_list = get_link(self.topology_api_app, None)

        for link in link_list:

            self.graph.add_edge(link.src.dpid, link.dst.dpid, weight=1, port=link.src.port_no)

            self.graph.add_edge(link.dst.dpid, link.src.dpid, weight=1, port=link.dst.port_no)

        switch_all_port = {}

        for switch in switch_list:

            dpid = switch.dp.id

            flag = False;

            for port in switch.ports:

                if flag:

                    switch_all_port[dpid].add(port.port_no)

                    continue    

                if not switch_all_port.get(dpid):

                    switch_all_port[dpid] = {port.port_no}

                    flag = True

            for link in link_list:

                Src = link.src

                Dst = link.dst

                if switch_all_port.get(Src.dpid):

                        switch_all_port[Src.dpid].discard(Src.port_no)

                if switch_all_port.get(Dst.dpid):

                        switch_all_port[Dst.dpid].discard(Dst.port_no)

            self.switch_host_port = switch_all_port

        print("nodes:",end='')

        print(self.graph.nodes())

        print("links:",end='')

        print(self.graph.edges())

        print("topo:",end='')

        print("n1  n2  weight")

        for u, adj_u in self.graph.adj.items():

            for v, eattr in adj_u.items():

                if u < v:

                    self.logger.info('%2s  %2s  %d', u, v, eattr['weight'])

        print("--------------------------------")
