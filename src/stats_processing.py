import queue
import json

# 类,函数使用驼峰命名；变量使用蛇形命名

def hello():
    print('i am in stats_processing module,oh yeah!!!')

stats = {} #存储过滤后的流表消息
set_pre_flow_entry = set() # 前一个时刻的流表
set_flow_entry = set() # 当前流表集
count_flow_entry = 0 # 当前流表,较上次有变化的流数


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

# 存最近100个元素，设为101,因为计算时要减掉自己的那一个

list_recent_entry = []
recent_entry_num = 101


# stats_msg为一个列表，它的每个元素是一个字典
# 该字典只有一个元素：键为dpid，值为msg.to_jsondict()
# 这么做是为了方便这里的接收。
def process(stats_msg):
#    print(json.dumps(stats_msg))
    stats = filterIcmpAndArp(stats_msg)

    print('current set_flow_entry len:',len(set_flow_entry))
    print('previous set_flow_entry len:',len(set_pre_flow_entry))

    print('current flow_entry')
    for elements in set_flow_entry:
        print(elements.__dict__)
#     print('previous flow_entry')
#     for elements in set_pre_flow_entry:
#         print(elements.__dict__)


    getEntryStatisticFeature()

    # 对当前流表中的所有流量有变化的流进行特征提取
    # 待实现统计量:流时间与流包数比；流字节数与流包数比(只在getEntryFeature中计算),当前流表中dIP,sIP,dPort熵
# 返回为一个列表:[proto,src_bytes,packet_count,count,srv_count,srv_diff_host_rate,dst_host_count,dst_host_srv_count,dst_host_srv_diff_host_rate,flow_duration,byte_count_ratio,packet_count_ratio,byte_count_inc,packet_count_inc]
def getEntryStatisticFeature():
    pre_entry_list = list(set_pre_flow_entry)
    count_flow_entry = 0 # 当前的流数
    list_feature = []
    for entry in set_flow_entry:
        byte_count_inc = entry.byte_count # 较上个time slot该流发送字节增长数
        packet_count_inc = entry.packet_count # 较上个time slot该流发送包数增长数
        
        if entry in pre_entry_list:
           index = pre_entry_list.index(entry)
           pre_entry = pre_entry_list[index]
           # print('current bytes:',entry.byte_count,'pre bytes:',pre_entry.byte_count)
           # 过滤掉没有包通过的流,因为若该流没有包通过则上个时间段已检测过因此没必要重复检测
           if entry.byte_count == pre_entry.byte_count:
               continue
           bytes_inc = entry.byte_count - pre_entry.byte_count
           packet_inc = entry.packet_count - pre_entry.packet_count
           
        # print('diff entry:',entry.__dict__)
        count_flow_entry = count_flow_entry + 1
        list_feature = list(getEntryFeature(entry))
        list_feature.append(byte_count_inc)
        list_feature.append(packet_count_inc)
        print(list_feature) #这里有个问题,for只会运行一次,需要修改
        
# 对于指定流获取它的特征
# 返回为一个元组:(proto,src_bytes,packet_count,count,srv_count,srv_diff_host_rate,dst_host_count,dst_host_srv_count,dst_host_srv_diff_host_rate,flow_duration,byte_count_ratio,packet_count_ratio)
def getEntryFeature(entry):
    proto = entry.proto
    src_bytes = entry.byte_count
    packet_count = entry.packet_count
    count = 0 # 本时间段内与当前连接目的地址相同的连接数
    srv_count = 0 #本时间段内与当前连接服务相同的连接数
    srv_diff_host_rate = 0 # 本时间段内服务相同,不同主机的百分比,它最好与count_flow_entry配合使用
    srv_diff_host_count = 0
    dst_host_count = 0 # 前100个连接与当前连接具有相同目标主机连接数
    global list_recent_entry # 声明该变量是全局的防止出现未定义错误
    dst_host_srv_count = 0 # 前100个连接与当前连接具有相同目的主机，相同服务数的连接个数
    dst_host_srv_diff_host_rate = 0 # 前100个连接相同目的主机，相同服务，不同源主机所占百分比
    dst_host_srv_diff_host_count = 0
    flow_duration = 0
    byte_count_ratio = 0
    packet_count_ratio = 0
    
    for element in set_flow_entry:
        if element.dIP == entry.dIP:
            count = count + 1

        if element.dPort == entry.dPort:
            srv_count = srv_count + 1
            if element.sIP != entry.sIP or element.dIP != element.dIP:
                srv_diff_host_count = srv_diff_host_count + 1
    # 减掉他自己            
    count = count - 1
    srv_count = srv_count - 1
    
    if srv_diff_host_count > 0:
        srv_diff_host_rate = srv_diff_host_count / len(set_flow_entry)
    
    for element in list_recent_entry:
        if element.dIP == entry.dIP:
            dst_host_count = dst_host_count + 1
            if element.dPort == entry.dPort:
                dst_host_srv_count = dst_host_srv_count + 1
                if element.sIP != entry.sIP:
                    dst_host_srv_diff_host_count = dst_host_srv_diff_host_count + 1

    dst_host_count = dst_host_count - 1
    dst_host_srv_count = dst_host_srv_count - 1
    #算它使用的不是真实最近流个数而是指定的个数，以防止流数不多时计算结果偏大的情况
    if dst_host_srv_diff_host_count > 0:  
        dst_host_srv_diff_host_rate = dst_host_srv_diff_host_count / recent_entry_num

    flow_duration = entry.duration_sec
    if flow_duration > 0:
        byte_count_ratio = src_bytes / flow_duration
        packet_count_ratio = packet_count / flow_duration
             
    return proto,src_bytes,packet_count,count,srv_count,srv_diff_host_rate,dst_host_count,dst_host_srv_count,dst_host_srv_diff_host_rate,flow_duration,byte_count_ratio,packet_count_ratio

        
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
                if body[key_OFPFlowStats][key_priority] == 5 and  body[key_OFPFlowStats][key_packet_count] != 0:
                    udpAndTcpBody.append(body)
                    # 通过观察它的msg.to_json_dicts获取priority为5的所有匹配项
                    # 并从匹配项中获取流id和统计值
                    matches = body[key_OFPFlowStats][key_match][key_OFPMatch][key_oxm_fields]
                    # 获取流表id，并根据该id创建流对象
                    sIP,dIP,sPort,dPort,pro = getFlowId(matches)
                    # 使用获得的流id创建对象，并对该对象赋属性值,并将该流存入set_flow_entry中
                    tempFlow = FlowEntry(sIP,dIP,sPort,dPort,pro)
                    tempFlow.duration_sec = body[key_OFPFlowStats][key_duration_sec]
                    tempFlow.byte_count = body[key_OFPFlowStats][key_byte_count]
                    tempFlow.packet_count = body[key_OFPFlowStats][key_packet_count]
                    set_flow_entry.add(tempFlow)

            OFPFlowStatsReply[key_body] = udpAndTcpBody
            flowStatsDict[dpid] = OFPFlowStatsReply
    # 获得当前流集与前一个time slot流集的差集,并保存最近100个以供计算流特征
    set_diff_entry = set_flow_entry.difference(set_pre_flow_entry)
    # 使用global声明，否则会出现“在定义前使用变量”的错误
    global list_recent_entry
    list_recent_entry.extend(list(set_diff_entry))
    list_recent_entry = list_recent_entry[-recent_entry_num:]
    print('len of list_recent_entry:',len(list_recent_entry))

    return flowStatsDict

# 参数为oxm_fields列表，它的每一项都是一个OXMTlv格式的流表匹配项，
# 通过解析流表匹配项返回流id五元组
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

# 流对象类，修改hash从而达到对流去重的效果
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
