import queue
import json

def hello():
    print('i am in stats_processing module,oh yeah!!!')

stats = {}

# stats_msg为一个列表，它的每个元素是一个字典
# 该字典只有一个元素：键为dpid，值为msg.to_jsondict()
# 这么做是为了方便这里的接收。
def process(stats_msg):
    print(json.dumps(stats_msg))
    stats = filterIcmpAndArp(stats_msg)
    print(json.dumps(stats))
    

def filterIcmpAndArp(stats_msg):
    # flow_stats为只有一个元素的字典，键为dpid，值为ev.msg.to_jsondict()
    stats_msg = stats_msg
    flowStatsDict = {}
    bodys = []
    dpid = ''
    
    for flow_stats in stats_msg:
        for dpid in flow_stats.keys():
           # 这里不要丢键，否则会导致提取结果为空
           OFPFlowStatsReply = flow_stats.get(dpid).get('OFPFlowStatsReply')
           bodys = OFPFlowStatsReply.get('body')
           if not bodys:
               continue
           udpAndTcpBody = []
           for body in bodys:
               # 这里又有一个键不要丢了
               if body['OFPFlowStats']['priority'] == 5:
                   udpAndTcpBody.append(body)

           OFPFlowStatsReply['body'] = udpAndTcpBody
           flowStatsDict[dpid] = OFPFlowStatsReply
    return flowStatsDict
        
