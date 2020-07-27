class WritePort():
    def __init__(self,path):
        self.path = path

    def writePort(self,file_name):
        file_name = self.path + file_name;
        with open(file_name,'w') as tmp_file:
            print('create file:',tmp_file)
            # 根据论文中的结果写入协义对应的端口号,第二列为连接平均产生数据小
            # http
            for i in range(10):
                tmp_file.write('80 2M')
                tmp_file.write('\n')
            # https
            for i in range(70):
                tmp_file.write('443 4M')
                tmp_file.write('\n')
            # ssh
            for i in range(2):
                tmp_file.write('22 500K')
                tmp_file.write('\n')
                
            # ftp
            for i in range(6):
                tmp_file.write('21 20 69 10M')
                tmp_file.write('\n')
                
            # email
            tmp_file.write('25 110 3M')
            tmp_file.write('\n')
            
            # other,当为0时,则从全部的1023个端口中找,1-5M随机发送
            for i in range(7):
                tmp_file.write('0 0')
                tmp_file.write('\n')                

if __name__ == '__main__':
    writer = WritePort('/home/hb/sdn/')
    writer.writePort('port')
