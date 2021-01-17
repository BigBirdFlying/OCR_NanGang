import os
import time
import json
#import win32file #需要安装pywin32的包

'''
def is_used(file_name):
	try:
		vHandle = win32file.CreateFile(file_name, win32file.GENERIC_READ, 0, None, win32file.OPEN_EXISTING, win32file.FILE_ATTRIBUTE_NORMAL, None)
		return int(vHandle) == win32file.INVALID_HANDLE_VALUE
	except:
		return True
	finally:
		try:
			win32file.CloseHandle(vHandle)
		except:
			pass
'''

def delete_file(log_oper,path_list):
    try:
        for file_path in path_list:
            if os.path.exists(file_path):
                os.remove(file_path)
                '''
                if is_used(file_path) is False:
                    os.remove(file_path)
                else:
                    for i in range(0,5):
                        time.sleep(0.1)
                        if is_used(file_path) is False:
                            os.remove(file_path)
                            break
                '''
                #log_oper.add_log("Normal>>删除图片路径：{}".format(file_path))
    except Exception as err:
        log_oper.add_log("Error>>图像删除过程中出现错误，错误代码为{}".format(err))

class Log:
    def __init__(self, log_dir_name):
        self.log_dir_name = log_dir_name
        if not os.path.exists(self.log_dir_name):
            os.mkdir(self.log_dir_name)

    def add_log(self, info):
        try:
            log_file_name = ((self.log_dir_name + "\%s.txt") % time.strftime("%Y%m%d"))
            cur_time = time.strftime("%H:%M:%S")
            log_info = ("%s: %s \n" % (cur_time, info))
            with open(log_file_name, 'a') as f:
                f.write(log_info)
            print_info(info)
        except Exception as err:
            pass

def print_info(info):
    cur_time = time.strftime("%H:%M:%S")
    log_info = ("%s: %s" % (cur_time, info))
    log_info=log_info.replace('\n',' ')
    print(log_info)
