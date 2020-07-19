from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib import dpid as dpid_lib
from ryu.topology import event
from ryu.topology.api import get_switch,get_link

from ryu.lib import hub
import networkx as nx
import queue
import json
import stats_processing


#                            _ooOoo_
#                           o8888888o
#                           88" . "88
#                           (| -_- |)
#                            O\ = /O
#                        ____/`---'\____
#                      .   ' \\| |// `.
#                       / \\||| : |||// \
#                     / _||||| -:- |||||- \
#                       | | \\\ - /// | |
#                     | \_| ''\---/'' | |
#                      \ .-\__ `-` ___/-. /
#                   ___`. .' /--.--\ `. . __
#                ."" '< `.___\_<|>_/___.' >'"".
#               | | : `- \`.;`\ _ /`;.`/ - ` : | |
#                 \ \ `-. \_ __\ /__ _/ .-` / /
#         ======`-.____`-.___\_____/___.-`____.-'======
#                            `=---='
#
#         .............................................
#                  佛祖镇楼                  Bug辟易
#          佛曰:
#                  写字楼里写字间，写字间里程序员；
#                  程序人员写程序，又拿程序换酒钱。
#                  酒醒只在网上坐，酒醉还来网下眠；
#                  酒醉酒醒日复日，网上网下年复年。
#                  但愿老死电脑间，不愿鞠躬老板前；
#                  奔驰宝马贵者趣，公交自行程序员。
#                  别人笑我忒疯癫，我笑自己命太贱；
#                  不见满街漂亮妹，哪个归得程序员？

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.ip_to_port = {}
        self.network = nx.DiGraph()
        self.paths = {} #store the shortest path
        self.topology_api_app = self

        self.datapaths = {}
        self.flow_stats_queue = queue.Queue()
        self.monitor_thread = hub.spawn(self._monitor)
        self.flow_stats_processing_thread = hub.spawn(self._flow_stats_processing)

    # 当有交换机添加或离去时及时更新datapaths[]的内容
    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self,ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('registering datapath:%s',dpid_lib.dpid_to_str(datapath.id))
                self.datapaths[datapath.id] = datapath
            elif ev.state == DEAD_DISPATCHER:
                if datapath.id in self.datapaths:
                    self.logger.debug('unregistering datapath:%s',dpid_lib.dpid_to_str(datapath.id))
                    del self.datapaths[datapath.id]
    
    #定期调用请求命令
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)
            self.logger.info('monitor is running!!!')
            self.logger.info('datapaths = %s',self.datapaths)

    #向datapath发送请求
    def _request_stats(self,datapath):
        self.logger.debug('send stats requests to:%s',
                          dpid_lib.dpid_to_str(datapath.id))
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    #流状态响应函数，将取到的值以字典的形式向放队列
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self,ev):
        body = ev.msg.body
        flow_stats = {}
        flow_stats[dpid_lib.dpid_to_str(ev.msg.datapath.id)] = ev.msg.to_jsondict()
        self.flow_stats_queue.put(flow_stats)
    
    # 每隔10s将队列中所有数据取出，并交给流状态处理函数处理
    def _flow_stats_processing(self):
        while True:
            stats_msg = []
            hub.sleep(10)
            while not self.flow_stats_queue.empty():
                stats_msg.append(self.flow_stats_queue.get())
            # self.logger.info(json.dumps(stats_msg))
            stats_processing.hello()
            stats_processing.process(json.dumps(stats_msg))

    #初始化流表
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst, idle_timeout=idle_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst,
                                    idle_timeout=idle_timeout)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        self.logger.info('packet_in handler is called!!!')
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        dpid_str = dpid_lib.dpid_to_str(datapath.id)
        # print(type(dpid_str))
        # print(dpid_str)
        
        pkt = packet.Packet(msg.data)
        # self.logger.info("packet_in is :%s",pkt)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if not eth:
            return

       #获得它的IP的源和目的地址,要先看高层协议
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        if pkt_ipv4:
            ipv4_src = pkt_ipv4.src
            ipv4_dst = pkt_ipv4.dst
            self.logger.info('get ipv4:src=%s,dst=%s,eth_src=%s,eth_dst=%s' % (pkt_ipv4.src,
                pkt_ipv4.dst,
                pkt.get_protocols(ethernet.ethernet)[0].src,
                pkt.get_protocols(ethernet.ethernet)[0].dst))
            self._packet_in_ip_handler(msg)
            return

        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            self._packet_in_arp_handler(msg)

    # 获取当前拓扑并将其存入network中
    @set_ev_cls(event.EventSwitchEnter,[CONFIG_DISPATCHER,MAIN_DISPATCHER])    #event is not from openflow protocol, is come from switchs` state changed, just like: link to controller at the first time or send packet to controller
    def get_topology(self,ev):
        '''
        get network topo construction, save info in the dict
        '''
        #store nodes info into the Graph
        switch_list = get_switch(self.topology_api_app,None)    #------------need to get info,by debug
        switches = [dpid_lib.dpid_to_str(switch.dp.id) for switch in switch_list]
        self.network.add_nodes_from(switches)

        #store links info into the Graph
        link_list = get_link(self.topology_api_app,None)
        #port_no, in_port    
        links = [(dpid_lib.dpid_to_str(link.src.dpid),dpid_lib.dpid_to_str(link.dst.dpid),{'attr_dict':{'port':link.src.port_no}}) for link in link_list]    #add edge, need src,dst,weigtht
        self.network.add_edges_from(links)

    # 使用stp获得输出端口    
    def get_out_port(self,datapath,src,dst,in_port):
        '''
        datapath: is current datapath info
        src,dst: both are the host info
        in_port: is current datapath in_port
        '''
        dpid = dpid_lib.dpid_to_str(datapath.id)

        #the first :Doesn`t find src host at graph
        if src not in self.network:
            self.logger.info("src %s not in network",src)
            self.network.add_node(src)
            self.network.add_edge(dpid, src, attr_dict={'port':in_port})
            self.network.add_edge(src, dpid)
            self.paths.setdefault(src, {})
        else:
            self.logger.info('src %s in network',src)

        #second: search the shortest path, from src to dst host
        if dst in self.network:
            if dst not in self.paths[src]:    #if not cache src to dst path,then to find it
                path = nx.shortest_path(self.network,src,dst)
                self.paths[src][dst]=path

            path = self.paths[src][dst]
            next_hop = path[path.index(dpid)+1]
            out_port = self.network[dpid][next_hop]['attr_dict']['port']
            #get path info
            print("dst in network,path is:",path)
        else:
            self.logger.info("dst %s not in network,out_port=flood",dst)
            out_port = datapath.ofproto.OFPP_FLOOD    #By flood, to find dst, when dst get packet, dst will send a new back,the graph will record dst info
        return out_port

    # packet_in包中是ip包处理函数    
    def _packet_in_ip_handler(self,msg):
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_icmpv4 = pkt.get_protocol(icmp.icmp)
        pkt_tcp = pkt.get_protocol(tcp.tcp)
        pkt_udp = pkt.get_protocol(udp.udp)

        if pkt_icmpv4:
            self._packet_icmp_handler(msg)

        if pkt_tcp:
            self.logger.info('get tcp packet')
            self._packet_tcp_handler(msg)

        if pkt_udp:
            self.logger.info('get udp packet')
            self._packet_udp_handler(msg)

    # packet_in包中udp包处理函数        
    def _packet_udp_handler(self,msg):
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        pkt_udp = pkt.get_protocol(udp.udp)
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        dpid = dpid_lib.dpid_to_str(datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        self.ip_to_port.setdefault(dpid,{})
        self.ip_to_port[dpid][pkt_ipv4.src] = in_port
        out_port = self.get_out_port(datapath,pkt_eth.src,pkt_eth.dst,in_port)

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(eth_dst=pkt_eth.dst,
                eth_type=pkt_eth.ethertype, 
                ipv4_src=pkt_ipv4.src,
                ipv4_dst=pkt_ipv4.dst, 
                ip_proto=pkt_ipv4.proto,
                udp_src=pkt_udp.src_port,
                udp_dst=pkt_udp.dst_port
                )
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.logger.info("in if!%s",out_port)
                self.add_flow(datapath, 5, match, actions, msg.buffer_id)
                return
            else:
                self.logger.info(out_port)
                self.add_flow(datapath, 5, match, actions)
                self.logger.info("add flow,dpid:%s,pkt_udp,%s",datapath.id,pkt_udp)
                self.logger.info(match)    
        else:
            self.logger.info('udp:out_port is ofproto.OFPP_FLOOD')       

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def _packet_tcp_handler(self,msg):
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        pkt_tcp = pkt.get_protocol(tcp.tcp)
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        dpid = dpid_lib.dpid_to_str(datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        out_port = self.get_out_port(datapath,pkt_eth.src,pkt_eth.dst,in_port)
        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(eth_dst=pkt_eth.dst,
                eth_type=pkt_eth.ethertype, 
                ipv4_src=pkt_ipv4.src,
                ipv4_dst=pkt_ipv4.dst, 
                ip_proto=pkt_ipv4.proto,
                tcp_src=pkt_tcp.src_port,
                tcp_dst=pkt_tcp.dst_port
                )
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 5, match, actions, msg.buffer_id)
                return
            else:
                self.logger.info(out_port)
                self.add_flow(datapath, 5, match, actions, idle_timeout=15)
                self.logger.info("tcp add flow,dpid:%s,timeout:15",datapath.id)
                self.logger.info(match)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)


    def _packet_icmp_handler(self,msg):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt = packet.Packet(msg.data)
        in_port = msg.match['in_port']
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_icmpv4 = pkt.get_protocol(icmp.icmp)

        dpid = dpid_lib.dpid_to_str(datapath.id)
        self.ip_to_port.setdefault(dpid,{})
        self.ip_to_port[dpid][pkt_ipv4.src] = in_port

        out_port = self.get_out_port(datapath,pkt_eth.src,pkt_eth.dst,in_port)
        # if pkt_ipv4.dst in self.ip_to_port[dpid]:
        #     out_port = self.ip_to_port[dpid][pkt_ipv4.dst]
        # else:
        #     out_port = ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(eth_dst=pkt_eth.dst,
                eth_type=pkt_eth.ethertype, 
                ipv4_dst=pkt_ipv4.dst, 
                ip_proto=pkt_ipv4.proto
                )
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 2, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 2, match, actions)
                self.logger.info("add icmp flow entry:pkt_ipv4.src:%s",pkt_ipv4.src)
                self.logger.info(match)           
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def _packet_in_arp_handler(self,msg):
        datapath = msg.datapath
        pkt_arp = packet.Packet(msg.data).get_protocol(arp.arp)
        pkt_eth = packet.Packet(msg.data).get_protocols(ethernet.ethernet)[0]

        # self.logger.info("pkt_arp:%s",pkt_arp)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        in_port = msg.match['in_port']
        dst = pkt_eth.dst
        src = pkt_eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
 
        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(eth_dst=pkt_arp.dst_mac,
                eth_type = pkt_eth.ethertype,
                arp_tpa = pkt_arp.dst_ip,
                arp_tha = pkt_arp.dst_mac)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
                self.logger.info("add flow:pkt_arp.src_mac:%s",pkt_arp.src_mac)
                # self.logger.info(match)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)


