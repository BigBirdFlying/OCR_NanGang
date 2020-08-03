import os
import time
import json

def delete_file(log_oper,path_list):
    try:
        for file_path in path_list:
            if os.path.exists(file_path):
                os.remove(file_path)
                log_oper.add_log("Normal>>删除图片路径：{}".format(file_path))
    except Exception as err:
        log_oper.add_log("Error>>删除图片时出现错误，错误代码为{}".format(err))

class Log:
    def __init__(self, log_dir_name):
        self.log_dir_name = log_dir_name
        if not os.path.exists(self.log_dir_name):
            os.mkdir(self.log_dir_name)

    def add_log(self, info):
        log_file_name = ((self.log_dir_name + "\%s.txt") % time.strftime("%Y%m%d"))
        cur_time = time.strftime("%H:%M:%S")
        log_info = ("%s: %s \n" % (cur_time, info))
        with open(log_file_name, 'a') as f:
            f.write(log_info)
        print_info(info)

def print_info(info):
    cur_time = time.strftime("%H:%M:%S")
    log_info = ("%s: %s" % (cur_time, info))
    log_info=log_info.replace('\n',' ')
    print(log_info)
