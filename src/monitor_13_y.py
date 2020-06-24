from operator import attrgetter
from ryu.app import simple_switch_13
from ryu.controller.handler import set_ev_cls
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.lib import hub
import json


class MyMonitor(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(MyMonitor, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.datas = {}
        self.ports = {}
        self.monitor_thread = hub.spawn(self._monitor)

    # receive port stats info
    # defend a map {key: dPid, value: dataPath} to save switch info in real time
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        # judge dataPaths status to decide operate
        if datapath.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath
                self.logger.debug("Regist datapath: %16x", datapath.id)
        elif datapath.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]
                self.logger.debug("Unregist datapath: %16x", datapath.id)

    # a sub thread to loop monitor traffic by 5s times
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            self.logger.info("######## datas ####### %s", self.datas)
            self.logger.info("######## ports ####### %s", self.ports)
            hub.sleep(5)

    # send request to dataPath for port and flow info
    def _request_stats(self, datapath):
        self.logger.debug("send stats reques to datapath: %16x for port and flow info", datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    # receive port status response handler
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        dp = []
        for port_stat in sorted(body, key=attrgetter('port_no')):
            pt = {}
            pt["port"] = port_stat.port_no
            pt["rx_packets"] = port_stat.rx_packets
            pt["rx_bytes"] = port_stat.rx_bytes
            pt["tx_packets"] = port_stat.tx_packets
            pt["tx_bytes"] = port_stat.tx_bytes
            dp.append(pt)
        self.ports[dpid] = dp

    # receive flow table status handler
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        # 1. get flow table msg
        dp = []
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        for flow_stat in sorted([flow for flow in body if flow.priority == 1],
                                key=lambda flow: (flow.match['in_port'], flow.match['eth_src'])):
            ft = {}
            ft["duration_sec"] = flow_stat.duration_sec + flow_stat.duration_nsec / (1000 * 1000 * 1000)
            ft["packet_count"] = flow_stat.packet_count
            ft["byte_count"] = flow_stat.byte_count
            ft["actions"] = {}
            ft["actions"]["out_port"] = flow_stat.instructions[0].actions[0].port
            ft["match"] = {}
            ft["match"]["in_port"] = flow_stat.match['in_port']
            ft["match"]["eth_src"] = flow_stat.match['eth_src']
            ft["match"]["eth_dst"] = flow_stat.match['eth_dst']
            # ft["match"]["ipv4_src"] = flow_stat.match['ipv4_src']
            # ft["match"]["ipv4_dst"] = flow_stat.match['ipv4_dst']
            dp.append(ft)
        self.datas[dpid] = dp

