# coding=utf-8
import threading, time, queue
q = queue.Queue()
def Produce(name):
    count = 0   #   conut表示做的包子总个数
    while count < 10:
        print('厨师%s在做包子中...'%name)
        time.sleep(1)
        q.put(count)   # 容器中添加包子
  # 当做完一个包子后就要给顾客发送一个信号,表示已经做完,让他们吃包子
        print('produce%s已经做好了第%s个包子'%(name, count))
        count += 1
        print('oking...')
def Consumer(name):
    count = 0    #  count表示包子被吃的总个数
    while count < 10:
        time.sleep(2)  #  排队去取包子,
        if not q.empty():   # 如果存在
            data = q.get() #  取包子, 吃包子
            print('\033[32;1mConsumer %s已经把第%s个包子吃了...\033[0m' %(name, data))
        else:
            print('包子被吃完了...')
        count += 1
if __name__ == '__main__':
    p1 = threading.Thread(target=Produce, args=('A君',))
    c1 = threading.Thread(target=Consumer, args=('B君',))
    c2 = threading.Thread(target=Consumer, args=('C君',))
    c3 = threading.Thread(target=Consumer, args=('D君',))
    p1.start()
    c1.start()
    c2.start()
    c3.start()