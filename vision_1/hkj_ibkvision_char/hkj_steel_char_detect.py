import os
import time
import cv2
import json
import socket
import threading
import numpy as np
import tensorflow as tf
from operator import itemgetter
from PIL import Image
from struct import pack,unpack,pack_into
from ctypes import create_string_buffer
from hkj_ibkvision_char.steel_unit.yolo import YOLO
from hkj_ibkvision_char.char_unit.model import efficientdet
from hkj_ibkvision_char.char_unit.init import preprocess_image, postprocess_boxes
from hkj_ibkvision_char.char_unit.draw_boxes import draw_boxes,nms

def delete_file(log_oper,path_list):
    for file_path in path_list:
        if os.path.exists(file_path):
            os.remove(file_path)
            log_oper.add_log("Normal>>删除图片路径：{}".format(file_path))

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
        print_info(log_info)

def print_info(info):
    cur_time = time.strftime("%H:%M:%S")
    log_info = ("%s: %s" % (cur_time, info))
    log_info=log_info.replace('\n',' ')
    print(log_info)

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

def rotate_bound(image, angle):
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    return cv2.warpAffine(image, M, (nW, nH))

def get_steel_info(boxes, scores, labels, classes):
    base_box=None
    char_boxs=[]
    char_width_mean=0
    char_height_mean=0
    char_width_n=0
    char_height_n=0
    for b, l, s in zip(boxes, labels, scores):
        class_id = int(l)
        score_id = float(s)
        xmin, ymin, xmax, ymax = list(map(int, b))
        temp_box=[xmin, ymin, xmax, ymax, classes[class_id],score_id]
        if classes[class_id]=='*':
            base_box=[xmin, ymin, xmax, ymax,classes[class_id],score_id]
        if classes[class_id]!='#' and classes[class_id]!='*':
            char_width_mean=char_width_mean+(xmax-xmin)
            char_height_mean=char_height_mean+(ymax-ymin)
            char_width_n=char_width_n+1
            char_height_n=char_height_n+1
        char_boxs.append(temp_box)
    if char_width_n>0 and char_height_n>0:
        char_width_mean=char_width_mean/char_width_n
        char_height_mean=char_height_mean/char_height_n
        if base_box is not None:
            base_x=(base_box[2]+base_box[0])/2
            base_y=(base_box[3]+base_box[1])/2
            #第一行数据
            one_row_boxs=[]
            offset_row_boxs=[]
            offset_row_boxs_min_y=9999
            for i in range(0,len(char_boxs)):
                center_x=(char_boxs[i][2]+char_boxs[i][0])/2
                center_y=(char_boxs[i][3]+char_boxs[i][1])/2
                if center_x>base_x:
                    if abs(center_y-base_y)<char_height_mean:
                        one_row_boxs.append(char_boxs[i])
                    else:
                        offset_row_boxs.append(char_boxs[i])
                        if center_y<offset_row_boxs_min_y:
                            offset_row_boxs_min_y=center_y
            one_row_boxs.sort(key=itemgetter(0), reverse=False)
            steel_no=''
            steel_no_score=0
            char_interval=0
            for i in range(0,len(one_row_boxs)):
                steel_no=steel_no+str(one_row_boxs[i][4])
                steel_no_score=steel_no_score+one_row_boxs[i][5]
                #print(str(one_row_boxs[i][4]),one_row_boxs[i][5])
                if i<len(one_row_boxs)-1:
                    char_interval=char_interval+max(0,one_row_boxs[i+1][0]-one_row_boxs[i][2])
                if len(steel_no)==14:
                    break
            #第二行数据        
            two_row_boxs=[]
            char_boxs=offset_row_boxs
            offset_row_boxs=[]
            base_y=offset_row_boxs_min_y
            offset_row_boxs_min_y=9999
            for i in range(0,len(char_boxs)):
                center_x=(char_boxs[i][2]+char_boxs[i][0])/2
                center_y=(char_boxs[i][3]+char_boxs[i][1])/2
                if center_x>base_x:
                    if abs(center_y-base_y)<char_height_mean:
                        two_row_boxs.append(char_boxs[i])
                    else:
                        offset_row_boxs.append(char_boxs[i])
                        if center_y<offset_row_boxs_min_y:
                            offset_row_boxs_min_y=center_y
            two_row_boxs.sort(key=itemgetter(0), reverse=False)
            steel_type=''
            char_interval=0
            for i in range(0,len(two_row_boxs)-1):
                steel_type=steel_type+str(two_row_boxs[i][4])
                char_interval=max(0,two_row_boxs[i+1][0]-two_row_boxs[i][2])
                if char_interval>char_width_mean/2:
                    break
            #第三行数据        
            three_row_boxs=[]
            char_boxs=offset_row_boxs
            offset_row_boxs=[]
            base_y=offset_row_boxs_min_y
            offset_row_boxs_min_y=9999
            for i in range(0,len(char_boxs)):
                center_x=(char_boxs[i][2]+char_boxs[i][0])/2
                center_y=(char_boxs[i][3]+char_boxs[i][1])/2
                if center_x>base_x:
                    if abs(center_y-base_y)<char_height_mean:
                        three_row_boxs.append(char_boxs[i])
                    else:
                        offset_row_boxs.append(char_boxs[i])
                        if center_y<offset_row_boxs_min_y:
                            offset_row_boxs_min_y=center_y
            three_row_boxs.sort(key=itemgetter(0), reverse=False)
            steel_size=''
            char_interval=0
            for i in range(0,len(three_row_boxs)-1):
                steel_size=steel_size+str(three_row_boxs[i][4])
                char_interval=max(0,three_row_boxs[i+1][0]-three_row_boxs[i][2])
                if char_interval>char_width_mean/2:
                    break
            #返回数据
            steel_no_score=steel_no_score/14
            #if char_interval<char_width_mean:
            return steel_no,steel_no_score,steel_type,steel_size
    return '',0,'',''
    
def send_to_l2(s,log_oper,steel_no,steel_type,steel_size,img_path,counter):
    steel_size_list=steel_size.split('X')
    thick,width,length=0,0,0
    if len(steel_size_list)==3:
        if is_number(steel_size_list[0]):
            thick=float(steel_size_list[0])
        if is_number(steel_size_list[1]):
            width=float(steel_size_list[1])
        if is_number(steel_size_list[2]):
            length=float(steel_size_list[2])
              
    log_oper.add_log("Normal>>钢板号：{} 钢种：{} 厚度：{} 宽度：{} 长度：{} 图片路径：{}".format(steel_no,steel_type,thick,width,length,img_path))
    buf = create_string_buffer(132)
    pack_into("hhhh", buf,0,12001,132,counter,4)
    pack_into("{}s".format(len(steel_no)), buf,8,bytes(steel_no.encode('utf-8')))
    pack_into("{}s".format(len(steel_type)), buf,28,bytes(steel_type.encode('utf-8')))
    pack_into("fff", buf,48,thick,width,length)
    pack_into("{}s".format(len(img_path)), buf,60,bytes(img_path.encode('utf-8')))
    s.send(buf.raw)

def thread_send_heartbeat(s,log_oper):
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

def thread_recv_info(s,log_oper):
    while True:
        recv=s.recv(10)
        value=struct.unpack("hhhhh", recv)
        log_oper.add_log("Normal>>接收到二级发送的数据："+str(value))

def steel_char_detect(path_1,path_2,path_3,path_4):
    Log_oper=Log("Log_ASC")
    
    Log_oper.add_log("Normal>>开始载入跟踪模型")
    try:
        steel_model = YOLO()
    except Exception as err:
        Log_oper.add_log("Error>>执行中出现错误{},程序自动重启".format(err))
        os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')
    Log_oper.add_log("Normal>>完成载入跟踪模型成功")

    Log_oper.add_log("Normal>>开始载入识别模型")
    try:
        phi = 2
        weighted_bifpn = True
        model_path = 'char_model/char_model.h5'
        image_sizes = (512, 640, 768, 896, 1024, 1280, 1408)
        image_size = image_sizes[phi]
        classes = {value['id']: value['name'] for value in json.load(open('char_model/char_class.json', 'r')).values()}
        num_classes = len(classes)
        score_threshold = 0.25
        colors = [np.random.randint(0, 256, 3).tolist() for _ in range(num_classes)]
        _, char_model = efficientdet(phi=phi,weighted_bifpn=weighted_bifpn,num_classes=num_classes,score_threshold=score_threshold)
        char_model.load_weights(model_path, by_name=True)
        char_model_param={'image_size':image_size,'classes':classes,'score_threshold':score_threshold,'colors':colors}
    except Exception as err:
        Log_oper.add_log("Error>>执行中出现错误{},程序自动重启".format(err))
        os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')
    Log_oper.add_log("Normal>>完成载入识别模型成功")
    
    Log_oper.add_log("Normal>>开始创建二级连接")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('191.168.162.192', 12001))
        send_heartbeat = threading.Thread(target=thread_send_heartbeat,args=(s,Log_oper,))
        send_heartbeat.start()
        recv_info = threading.Thread(target=thread_recv_info,args=(s,Log_oper,))
        recv_info.start()
    except Exception as err:
        Log_oper.add_log("Error>>执行中出现错误{},程序自动重启".format(err))
        os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')
    Log_oper.add_log("Normal>>完成成功连接到二级")

    last_steel_no="00000000000000"
    judge_num=0
    counter=0
    cache_num=0
    cache_char=[]
    path_camera=path_1["path_camera"]
    path_steel=path_1["path_steel"]
    path_char=path_1["path_char"]
    path_char_l2=path_1["path_char_l2"]
    while True:
        img_path_list=[]
        Log_oper.add_log("Normal>>获得文件夹图像路径列表")
        for root,dirs,files in os.walk(path_camera):
            time.sleep(1)
            img_path_list=[]
            #确定是否钢板已走完
            if len(files)>0:
                judge_num=0
            else:
                judge_num=judge_num+1
            for file in files:
                if os.path.splitext(file)[1]=='.jpg':
                    src_img_path = os.path.join(path_camera,file)
                    img_path_list.append(src_img_path)
                    Log_oper.add_log("Normal>>开始处理{}的图像".format(src_img_path))
                    start = time.time()
                    try:
                        src_image_Image = Image.open(src_img_path)
                        src_image_Opencv=np.asarray(src_image_Image)
                        src_image_width,src_image_height=src_image_Image.size[0],src_image_Image.size[1]
                    except:
                        Log_oper.add_log("Error>>文件打开错误，直接跳过")
                        time.sleep(1)
                        continue
                    else:
                        try:
                            r_image,result = steel_model.detect_image(src_image_Image)
                            is_save=False
                            for n in range(0,len(result)):
                                (top,left,bottom,right)=result[n]['box']
                                to_top=top-0
                                to_bottom=src_image_height-bottom
                                roi_w=right-left
                                to_left=left-0
                                to_right=src_image_width-right
                                if roi_w>src_image_width*0.2 and to_left>src_image_width*0.15 and to_right>src_image_width*0.15 and to_top>=0 and to_bottom>=0 and result[n]['class']!='tchar':
                                    #存在字符则进行存储
                                    datetime=time.strftime("%Y%m%d")
                                    save_src_path = ((path_steel + "\%s") % datetime)
                                    if not os.path.exists(save_src_path):
                                        os.mkdir(save_src_path)
                                    save_src_img_path = os.path.join(save_src_path,file)
                                    cv2.imwrite(save_src_img_path,src_image_Opencv)
                                    Log_oper.add_log("Normal>>图像上存在字符，图像保存")

                                    #判断字符是否为倒置
                                    judge_char_inv=False
                                    #if bottom<src_image_height/2:
                                    #    judge_char_inv=True
                                    if result[n]['class']=='unchar':
                                        judge_char_inv=True
                                    if judge_char_inv is True:
                                        src_image_Opencv=rotate_bound(src_image_Opencv,180)
                                        top,bottom=src_image_height-bottom,src_image_height-top
                                        left,right=src_image_width-right,src_image_width-left
                                        Log_oper.add_log("Normal>>检测到字符为倒置状态，进行翻转")

                                    #拓展图像  
                                    left=max(0,left-0)
                                    right=min(src_image_width,right+0)
                                    roi_w=right-left
                                    top_s,bottom_s=top,bottom
                                    for i in range(0,src_image_height):
                                        top=max(0,top-1)
                                        bottom=min(src_image_height,bottom+1)
                                        roi_h=bottom-top
                                        if roi_h>=roi_w or roi_h>=src_image_height:
                                            break
                                    top_offset=abs(top_s-top)
                                    bottom_offset=abs(bottom_s-bottom)
                                    char_roi=src_image_Opencv[int(top):int(bottom),int(left):int(right)]
                                    Log_oper.add_log("Normal>>成功获得字符ROI")
                                    src_char_roi = char_roi.copy()
                                    char_roi = char_roi[:, :, ::-1]
                                    char_roi_h, char_roi_w = char_roi.shape[:2]
                                    char_roi_norm, scale = preprocess_image(char_roi, image_size=image_size)
                                    boxes, scores, labels = char_model.predict_on_batch([np.expand_dims(char_roi_norm, axis=0)])
                                    boxes, scores, labels = np.squeeze(boxes), np.squeeze(scores), np.squeeze(labels)                                
                                    boxes = postprocess_boxes(boxes=boxes, scale=scale, height=char_roi_h, width=char_roi_w)

                                    indices = np.where(scores[:] > score_threshold)[0]
                                    boxes = boxes[indices]
                                    labels = labels[indices]
                                    scores = scores[indices]

                                    res_nms = nms(boxes, scores, 0.1)
                                    boxes = boxes[res_nms]
                                    labels = labels[res_nms]
                                    scores = scores[res_nms]
                                    draw_boxes(src_char_roi, boxes, scores, labels, colors, classes)

                                    #整理字符
                                    steel_no,steel_no_score,steel_type,steel_size=get_steel_info(boxes, scores, labels, classes)
                                    steel_no=steel_no.replace("B","8")
                                    steel_no=steel_no.replace("D","0")
                                    steel_no=steel_no.replace("I","1")
                                    steel_no=steel_no.replace("O","0")
                                    steel_no=steel_no.replace("S","5")
                                    exist_char=True
                                    if len(steel_no) != 14:
                                        Log_oper.add_log("Warning>>当前识别钢板号{}不符合规则，放弃发送({})".format(steel_no,file))
                                        exist_char=False
                                    if False==steel_no.isdigit():
                                        Log_oper.add_log("Warning>>当前识别钢板号{}未全部由数字组成，放弃发送({})".format(steel_no,file))
                                        exist_char=False
                                    if exist_char is True:
                                        cache_char.append([steel_no,steel_no_score,steel_type,steel_size,src_char_roi,char_roi,top_offset,bottom_offset,file])
                            #缓存字符统一处理
                            cache_num=cache_num+1                                                                    
                            if len(cache_char)<=0:
                                continue
                            if len(result)>0 and cache_num<10:
                                continue
                            cache_char.sort(key=itemgetter(1), reverse=True)
                            steel_no,steel_no_score,steel_type,steel_size,src_char_roi,char_roi,top_offset,bottom_offset,file=cache_char[0]
                            cache_num=0
                            cache_char=[]
                            
                            if last_steel_no==steel_no:
                                Log_oper.add_log("Normal>>当前识别钢板号{}已发送过，无需再次发送({})".format(steel_no,file))
                                continue
                            last_steel_no=steel_no

                            #保存带标签的图片到本地
                            char_roi_h, char_roi_w = char_roi.shape[:2]
                            src_char_roi_cut=src_char_roi[max(int(0+top_offset)-10,0):min(int(char_roi_h-bottom_offset)+50,char_roi_h),:]
                            save_char_img_path = os.path.join(path_char,file)
                            cv2.imwrite(save_char_img_path,src_char_roi_cut)
                            Log_oper.add_log("Normal>>成功保存字符识别效果图")

                            #保存字符图片到二级发送文件夹
                            #char_roi_cut=char_roi[int(0+top_offset):int(char_roi_h-bottom_offset),:]
                            char_roi_cut_resize=cv2.resize(char_roi,(char_roi.shape[1],int(char_roi.shape[1]*0.75)))
                            datetime=time.strftime("%Y%m%d")
                            path_char_l2_curr = ((path_char_l2 + "\%s") % datetime)
                            if not os.path.exists(path_char_l2_curr):
                                os.mkdir(path_char_l2_curr)
                            save_l2_char_img_path = os.path.join(path_char_l2_curr,file)
                            cv2.imwrite(save_l2_char_img_path,char_roi_cut_resize)
                            Log_oper.add_log("Normal>>成功保存字符到二级文件夹")

                            #保存样本
                            save_sample_path = r"D:\ArNTCameraImage\Camera_No1\CameraImg_src"
                            save_sample_path_curr = ((save_sample_path + "\%s") % datetime)
                            if not os.path.exists(save_sample_path_curr):
                                os.mkdir(save_sample_path_curr)
                            save_sample_path_curr_img = os.path.join(save_sample_path_curr,file)
                            cv2.imwrite(save_sample_path_curr_img,src_image_Opencv)

                            #发送到L2
                            counter=counter+1
                            if counter>30000:
                                counter=1
                            send_to_l2(s,Log_oper,steel_no,steel_type,steel_size,os.path.join(datetime,file),counter)
                            Log_oper.add_log("Normal>>识别字符发送到二级")
                                    
                        except Exception as err:
                            Log_oper.add_log("Error>>执行中出现错误{}".format(err))
                            time.sleep(1)
                            continue
                        else:
                            pass
                Log_oper.add_log("Normal>>完成处理{}的图像，共用时{}秒".format(src_img_path,time.time() - start))
            #钢板走完直接发送字符，不受缓冲数量限制
            if judge_num>5:
                if len(cache_char)>0:
                    try:
                        Log_oper.add_log("Normal>>钢板已走完，图像数量未达到缓存数量，直接进行判断")
                        cache_char.sort(key=itemgetter(1), reverse=True)
                        steel_no,steel_no_score,steel_type,steel_size,src_char_roi,char_roi,top_offset,bottom_offset,file=cache_char[0]
                        cache_num=0
                        cache_char=[]
                        
                        if last_steel_no==steel_no:
                            Log_oper.add_log("Normal>>当前识别钢板号{}已发送过，无需再次发送({})".format(steel_no,file))
                            continue
                        last_steel_no=steel_no

                        #保存带标签的图片到本地
                        char_roi_h, char_roi_w = char_roi.shape[:2]
                        src_char_roi_cut=src_char_roi[max(int(0+top_offset)-10,0):min(int(char_roi_h-bottom_offset)+50,char_roi_h),:]
                        save_char_img_path = os.path.join(path_char,file)
                        cv2.imwrite(save_char_img_path,src_char_roi_cut)
                        Log_oper.add_log("Normal>>成功保存字符识别效果图")

                        #保存字符图片到二级发送文件夹
                        #char_roi_cut=char_roi[int(0+top_offset):int(char_roi_h-bottom_offset),:]
                        char_roi_cut_resize=cv2.resize(char_roi,(char_roi.shape[1],int(char_roi.shape[1]*0.75)))
                        datetime=time.strftime("%Y%m%d")
                        path_char_l2_curr = ((path_char_l2 + "\%s") % datetime)
                        if not os.path.exists(path_char_l2_curr):
                            os.mkdir(path_char_l2_curr)
                        save_l2_char_img_path = os.path.join(path_char_l2_curr,file)
                        cv2.imwrite(save_l2_char_img_path,char_roi_cut_resize)
                        Log_oper.add_log("Normal>>成功保存字符到二级文件夹")

                        #发送到L2
                        counter=counter+1
                        if counter>30000:
                            counter=1
                        send_to_l2(s,Log_oper,steel_no,steel_type,steel_size,os.path.join(datetime,file),counter)
                        Log_oper.add_log("Normal>>识别字符发送到二级")
                                
                    except Exception as err:
                        Log_oper.add_log("Error>>执行中出现错误{}".format(err))
                        time.sleep(1)
                        continue
                    else:
                        pass
            delete_file(Log_oper,img_path_list)
    steel_model.close_session()
