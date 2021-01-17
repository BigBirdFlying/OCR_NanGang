import copy
import threading
import time

class HThreadRecvInfo(threading.Thread):
    def __init__(self, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.s = args
        self.res = {"SBM":[1,1,1],"HTF1":[1,1,1],"HTF2":[1,1,1],"PRINT":[1,1,1]}  
    def run(self):
        num=1
        while True:  
            self.res["SBM"][0]=num
            num=num+1
            time.sleep(0.5)
 
    def get_result(self):
        return self.res

t_recv_info=HThreadRecvInfo((1,),"recv")       
t_recv_info.start() 


res= copy.deepcopy(t_recv_info.get_result())
res_last= copy.deepcopy(t_recv_info.get_result())
time.sleep(2)
def update():
    global res
    res= copy.deepcopy(t_recv_info.get_result())
    res_last["SBM"][0]=100
    print(res)
    
update()
print(res)
print(res_last)
