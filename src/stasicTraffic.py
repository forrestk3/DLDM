from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import CONFIG_DISPATCHER,MAIN_DISPATCHER
from ryu.lib.packet import *

class SelfLearnSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self,*args,**kwargs):
        super(SelfLearnSwitch,self).__init__(*args,**kwargs)
        self.Mac_Port_Table={}
		self.datas = []


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures)
    def switch_features_handler(self,ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        self.logger.info("datapath: %s link to controller",datapath.id)

        #table-miss
        match = ofp_parser.OFPMatch()   
        actions = [ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]    
        self.add_flow(datapath,0,match,actions,"table-miss")

    def add_flow(self,datapath,priority,match,actions,extra_info):
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        inst = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
        mod = ofp_parser.OFPFlowMod(datapath=datapath,priority=priority,match=match,instructions=inst)
        print("send "+extra_info)
        datapath.send_msg(mod)
	

    @set_ev_cls(ofp_event.EventOFPPacketIn,MAIN_DISPATCHER)
    def packet_in_handler(self,ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        dpid = datapath.id
        self.Mac_Port_Table.setdefault(dpid, {})

        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src
	    in_port = msg.match['in_port']
		
		#statis traffic 
		pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
		pkt_ipv6 = pkt.get_protocol(ipv6.ipv6)
		pkt_tcp = pkt.get_protocol(tcp.tcp)
		pkt_udp = pkt.get_protocol(udp.udp)
		
		# no consider ipv6
		rows = []	
		if pkt_ipv4 is not None:
			rows.append(src)
			rows.append(dst)
			rows.append(pkt_ipv4.src)
			rows.append(pkt_ipv4.dst)
			rows.append(pkt_ipv4.proto)
			rows.append(pkt_ipv4.total_length)
			rows.append(pkt_ipv4.ttl)

			if pkt_tcp is not None:
				rows.append(pkt_tcp.src_port)
				rows.append(pkt_tcp.dst_port)
			elif pkt_udp is not None:
				rows.append(pkt_udp.src_port)
				rows.append(pkt_udp.dst_port)
			self.datas.append(rows)
			rows = []
		
		# print log msg
		self.logger.info("  _packet_in_handler: datas -> %s", self.datas)
		self.logger.info(eth_pkt)
		self.logger.info("  _packet_in_handler: src_mac -> %s",  eth_pkt.src)
		self.logger.info("  _packet_in_handler: dst_mac -> %s",  eth_pkt.dst)
	
		# ipv4 
		self.logger.info("  _packet_in_handler: ipv4    -> %s",  pkt_ipv4)
		if pkt_ipv4 is not None:
			self.logger.info("ipv4 %s %s %s %s", pkt_ipv4.src, pkt_ipv4.dst, pkt_ipv4.ttl, pkt_ipv4.flags)

		# ipv6
		self.logger.info("  _packet_in_handler: ipv6    -> %s",  pkt_ipv6)
		if pkt_ipv6 is not None:
			self.logger.info("ipv6 %s %s", pkt_ipv6.src, pkt_ipv6.dst)	

		# tcp
		self.logger.info("  _packet_in_handler: tcp     -> %s",  pkt_tcp)
		if pkt_tcp is not None:
			self.logger.info("tcp %s %s", pkt_tcp.src_port, pkt_tcp.dst_port)

		# udp
		self.logger.info("  _packet_in_handler: udp     -> %s", pkt_udp)
		if pkt_udp is not None:
			self.logger.info("udp %s %s", pkt_udp.src_port, pkt_udp.dst_port)

		self.logger.info('  ------')
		self.logger.info("Controller receive the %s Switch from %s to %s and in_port %s",dpid,src,dst,in_port)
		
		
		# learnSwitch  
        self.Mac_Port_Table[dpid][src] = in_port
        if dst in self.Mac_Port_Table[dpid]:
            Out_Port = self.Mac_Port_Table[dpid][dst]
        else:
            Out_Port = ofproto.OFPP_FLOOD
			
        actions = [ofp_parser.OFPActionOutput(Out_Port)]
		
		# send flow table 
        if Out_Port != ofproto.OFPP_FLOOD:
            match = ofp_parser.OFPMatch(in_port=in_port,eth_dst = dst)
            self.add_flow(datapath, 1, match, actions,"a new flow entry by specify port")
            self.logger.info("send packet to switch port: %s",Out_Port)
		
		# send packet-out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = ofp_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
