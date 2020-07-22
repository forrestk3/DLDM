import queue
import json

# 类,函数使用驼峰命名；变量使用蛇形命名

def hello():
    print('i am in stats_processing module,oh yeah!!!')

stats = {} #存储过滤后的流表消息
set_pre_flow_entry = set() # 前一个时刻的流表
set_flow_entry = set() # 当前流表集

# 定义几个键常量
key_OFPFlowStatsReply = 'OFPFlowStatsReply'
key_body = 'body'
key_OFPFlowStats = 'OFPFlowStats'
key_match = 'match'
key_OFPMatch = 'OFPMatch'
key_oxm_fields = 'oxm_fields'
key_OXMTlv = 'OXMTlv'
key_priority = 'priority'

# flow id key
key_ipv4_src = 'ipv4_src'
key_ipv4_dst = 'ipv4_dst'
key_ip_proto = 'ip_proto'
key_udp_src = 'udp_src'
key_udp_dst = 'udp_dst'
key_tcp_src = 'tcp_src'
key_tcp_dst = 'tcp_dst'

# flow feature key
key_duration_sec = 'duration_sec'
key_packet_count = 'packet_count'
key_byte_count = 'byte_count'

# stats_msg为一个列表，它的每个元素是一个字典
# 该字典只有一个元素：键为dpid，值为msg.to_jsondict()
# 这么做是为了方便这里的接收。
def process(stats_msg):
    print(json.dumps(stats_msg))
    stats = filterIcmpAndArp(stats_msg)

    print('alen:',len(set_flow_entry))
    print('blen:',len(set_pre_flow_entry))

    print('current flow_entry')
    for elements in set_flow_entry:
        print(elements.__dict__)
    print('previous flow_entry')
    for elements in set_pre_flow_entry:
        print(elements.__dict__)
        
def filterIcmpAndArp(stats_msg):
    # flow_stats为只有一个元素的字典，键为dpid，值为ev.msg.to_jsondict()
    stats_msg = stats_msg
    flowStatsDict = {}
    bodys = []
    dpid = ''
    
    # 保存前一个时期的流表,并将当前流表集清空
    set_pre_flow_entry.clear()
    for elements in set_flow_entry:
        set_pre_flow_entry.add(elements)
    set_flow_entry.clear()
    
    for flow_stats in stats_msg:
        for dpid in flow_stats.keys():
            # 这里不要丢键，否则会导致提取结果为空
            OFPFlowStatsReply = flow_stats.get(dpid).get(key_OFPFlowStatsReply)
            bodys = OFPFlowStatsReply.get(key_body)
            if not bodys:
                continue
            udpAndTcpBody = []
            for body in bodys:
                # 这里又有一个键不要丢了
                if body[key_OFPFlowStats][key_priority] == 5:
                    udpAndTcpBody.append(body)
                    # 通过观察它的msg.to_json_dicts获取priority为5的所有匹配项
                    # 并从匹配项中获取流id和统计值
                    matches = body[key_OFPFlowStats][key_match][key_OFPMatch][key_oxm_fields]

                    sIP,dIP,sPort,dPort,pro = getFlowId(matches)

                    tempFlow = FlowEntry(sIP,dIP,sPort,dPort,pro)
                    tempFlow.duration_sec = body[key_OFPFlowStats][key_duration_sec]
                    tempFlow.byte_count = body[key_OFPFlowStats][key_byte_count]
                    tempFlow.packet_count = body[key_OFPFlowStats][key_packet_count]
                    set_flow_entry.add(tempFlow)
#                    set_pre_flow_entry.add(tempFlow)
            OFPFlowStatsReply[key_body] = udpAndTcpBody
            flowStatsDict[dpid] = OFPFlowStatsReply

    return flowStatsDict

# 参数为oxm_fields列表，它的每一项都是一个OXMTlv格式的流表匹配项
def getFlowId(oxm_fields):
    sIP = None
    dIP = None
    sPort = None
    dPort = None
    proto = None

    
    for element_OXMTlv in oxm_fields:
        # print('**********************')
        # print(element_OXMTlv)
        # print('**********************')
        
        dict_OXMTlv = element_OXMTlv.get(key_OXMTlv)
        
        if dict_OXMTlv.get('field') == key_ipv4_src:
            sIP = dict_OXMTlv.get('value')
        elif dict_OXMTlv.get('field') == key_ipv4_dst:
            dIP = dict_OXMTlv.get('value')
        elif dict_OXMTlv.get('field') == key_udp_src or dict_OXMTlv.get('field') == key_tcp_src:
            sPort = dict_OXMTlv.get('value')
        elif dict_OXMTlv.get('field') == key_udp_dst or dict_OXMTlv.get('field') == key_tcp_dst:
            dPort = dict_OXMTlv.get('value')
        elif dict_OXMTlv.get('field') == key_ip_proto:
            proto = dict_OXMTlv.get('value')
        else:
            continue
    return sIP,dIP,sPort,dPort,proto


class FlowEntry:
    sIP = None
    dIP = None
    sPort = None
    dPort = None
    proto = None

    duration_sec = 0
    byte_count = 0
    packet_count = 0

    def __init__(self,sIP = None,dIP = None,sPort = None,dPort = None,proto = None):
        self.sIP = sIP
        self.dIP = dIP
        self.sPort = sPort
        self.dPort = dPort
        self.proto = proto

    def getSIP(self):
        return self.sIP

    def getDIP(self):
        return self.dIP

    def isSymFlow(self,other):
        return self.sIP == other.dIP and self.dIP == other.sIP and self.sPort == other.dPort and self.dPort == other.sPort and self.proto == other.proto
    
    def __eq__(self,other):
        if isinstance(other,self.__class__):
            return self.sIP == other.getSIP() and self.dIP == other.getDIP() and self.sPort == other.sPort and self.dPort == other.dPort and self.proto == other.proto
        else:
            return False

    def __hash__(self):
        hash_str = self.sIP + self.dIP + str(self.sPort) + str(self.dPort) + str(self.proto)
        return hash(hash_str)
