import os
import time
import socket
import threading
from struct import pack,unpack,pack_into
from ctypes import create_string_buffer

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

def send_to_l2(s,log_oper,steel_no,steel_type,steel_size,img_path,counter,mark):
    if mark==1:
        steel_size_list=steel_size.split('X')
        thick,width,length=0,0,0
        if len(steel_size_list)==3:
            if is_number(steel_size_list[0]):
                thick=float(steel_size_list[0])
            if is_number(steel_size_list[1]):
                width=float(steel_size_list[1])
            if is_number(steel_size_list[2]):
                length=float(steel_size_list[2])
                  
        log_oper.add_log("Normal>>{}号识别点-> 钢板号：{} 钢种：{} 厚度：{} 宽度：{} 长度：{} 图片路径：{}".format(mark,steel_no,steel_type,thick,width,length,img_path))
        buf = create_string_buffer(132)
        pack_into("hhhh", buf,0,12000+int(mark),132,counter,3+int(mark))
        pack_into("{}s".format(len(steel_no)), buf,8,bytes(steel_no.encode('utf-8')))
        pack_into("{}s".format(len(steel_type)), buf,28,bytes(steel_type.encode('utf-8')))
        pack_into("fff", buf,48,thick,width,length)
        pack_into("{}s".format(len(img_path)), buf,60,bytes(img_path.encode('utf-8')))
        s.send(buf.raw)
    else:        
        log_oper.add_log("Normal>>{}号识别点-> 钢板号：{} 图片路径：{}".format(mark,steel_no,img_path))
        buf = create_string_buffer(100)
        pack_into("hhhh", buf,0,12000+int(mark),100,counter,3+int(mark))
        pack_into("{}s".format(len(steel_no)), buf,8,bytes(steel_no.encode('utf-8')))
        pack_into("{}s".format(len(img_path)), buf,28,bytes(img_path.encode('utf-8')))
        s.send(buf.raw)

def thread_send_heartbeat_to_l2(s,log_oper):
    buf = create_string_buffer(8)
    counter=0
    while True:
        try:
            counter=counter+1
            if counter>1000:
                counter=1
            pack_into("hhhh", buf,0,12005,8,counter,8)
            s.send(buf.raw)
            log_oper.add_log("Normal>>发送心跳信号")
            time.sleep(10)
        except:
            log_oper.add_log("Error>>二级通讯出现异常，程序自动重启")
            os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')

def thread_recv_info_from_l2(s,log_oper):
    while True:
        recv=s.recv(10)
        value=unpack("hhhhh", recv)
        log_oper.add_log("Normal>>接收到二级发送的数据："+str(value))

class HThreadRecvInfo(threading.Thread):
    def __init__(self, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.s,self.log_oper = args
        self.res = [1,1,1,1]
        
    def run(self):
        while True:
            recv=self.s.recv(10)
            value=unpack("hhhhh", recv)
            self.res[int(value[-2])]=int(value[-1])
            self.log_oper.add_log("Normal>>接收到二级发送的数据："+str(value))
            self.log_oper.add_log("Normal>>当前各识别点状态：{}".format(self.res))
 
    def get_result(self):
        try:
            return self.res
        except Exception:
            return None
