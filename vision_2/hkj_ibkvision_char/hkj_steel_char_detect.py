import os
import time
import cv2
import json
import copy
import socket
import threading
import numpy as np
import tensorflow as tf
from operator import itemgetter
from shutil import copyfile
from PIL import Image
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
from struct import pack,unpack,pack_into
from ctypes import create_string_buffer
from hkj_ibkvision_char.hkj_file_oper import Log,delete_file,print_info
from hkj_ibkvision_char.hkj_img_oper import rotate_bound
from hkj_ibkvision_char.hkj_char_oper import get_steel_info,get_steel_info_mini
from hkj_ibkvision_char.hkj_signal_oper import send_to_l2,thread_send_heartbeat_to_l2,thread_recv_info_from_l2,HThreadRecvInfo
from hkj_ibkvision_char.steel_unit.yolo import YOLO
from hkj_ibkvision_char.char_unit.model import efficientdet
from hkj_ibkvision_char.char_unit.init import preprocess_image, postprocess_boxes
from hkj_ibkvision_char.char_unit.draw_boxes import draw_boxes,nms


class SteelCharDetect:
    
    def __init__(self,mark,log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,sock,max_cache_num,path):
        self.mark=mark
        self.log_oper=log_oper
        self.steel_model=steel_model
        self.char_model=char_model
        self.char_model_param=char_model_param
        self.char_model_mini=char_model_mini
        self.char_model_param_mini=char_model_param_mini
        self.sock=sock
        self.max_cache_num=max_cache_num
        self.path_camera=path["path_camera"]
        self.path_ref=path["path_ref"]
        self.path_steel=path["path_steel"]
        self.path_char=path["path_char"]
        self.path_char_l2=path["path_char_l2"]
        self.cache_num_index=0
        self.cache_char=[]
        self.curr_char_img_info=[None,None]
        self.last_steel_no="00000000000000"
        self.counter=0
        
    def detect_steel(self,img_name):
        char_roi=None
        char_label=''
        top_offset,bottom_offset=0,0
        try:
            img_path = os.path.join(self.path_ref,img_name)
            self.log_oper.add_log("Normal>>开始检测{}的图像是否存在字符".format(img_path))
            start = time.time()
            src_image_Image = Image.open(img_path)
            src_image_Opencv=np.asarray(src_image_Image)
            src_image_width,src_image_height=src_image_Image.size[0],src_image_Image.size[1]
        except Exception as err:
            self.log_oper.add_log("Error>>文件打开错误，直接跳过，错误代码为{}".format(err))
        else:
            try:
                r_image,result = self.steel_model.detect_image(src_image_Image)
                self.cache_num_index=self.cache_num_index+1
                max_area=0
                for n in range(0,len(result)):
                    (top,left,bottom,right)=result[n]['box']
                    to_top=top-0
                    to_bottom=src_image_height-bottom
                    to_left=left-0
                    to_right=src_image_width-right
                    roi_w=right-left
                    roi_h=bottom-top
                    roi_a=roi_w*roi_h
                    
                    if roi_w>src_image_width*0.2 and to_left>src_image_width*0.15 and to_right>src_image_width*0.15 and to_top>=0 and to_bottom>=0:
                        #存在字符则进行存储
                        datetime=time.strftime("%Y%m%d")
                        save_img_path = ((self.path_steel + "\%s") % datetime)
                        if not os.path.exists(save_img_path):
                            os.mkdir(save_img_path)
                        save_img_path_name = os.path.join(save_img_path,img_name)
                        cv2.imwrite(save_img_path_name,src_image_Opencv)
                        self.log_oper.add_log("Normal>>图像上存在字符，图像保存")

                        #判断字符是否为倒置
                        if result[n]['class']=='unchar':
                            src_image_Opencv=rotate_bound(src_image_Opencv,180)
                            top,bottom=src_image_height-bottom,src_image_height-top
                            left,right=src_image_width-right,src_image_width-left
                            self.log_oper.add_log("Normal>>检测到字符为倒置状态，进行翻转")

                        #拓展图像
                        if result[n]['class']=='unchar' or result[n]['class']=='char':
                            left=max(0,left-0)
                            right=min(src_image_width,right+0)
                        else:
                            left=max(0,left-200)
                            right=min(src_image_width,right+200)
                        roi_w=right-left
                        top_s,bottom_s=top,bottom
                        for i in range(0,src_image_height):
                            top=max(0,top-1)
                            bottom=min(src_image_height,bottom+1)
                            roi_h=bottom-top
                            if roi_h>=roi_w or roi_h>=src_image_height:
                                break
                        
                        if roi_a>max_area:
                            max_area=roi_a
                            top_offset=abs(top_s-top)
                            bottom_offset=abs(bottom_s-bottom)
                            char_roi=src_image_Opencv[int(top):int(bottom),int(left):int(right)]
                            char_label=result[n]['class']
                            self.curr_char_img_info[0],self.curr_char_img_info[1]=img_name,char_roi
                            self.log_oper.add_log("Normal>>成功获得字符ROI")
                end = time.time()
                self.log_oper.add_log("Normal>>完成检测{}的图像是否存在字符，共用时{}秒".format(img_path,end-start))
            except Exception as err:
                self.log_oper.add_log("Error>>识别钢板是否存在字符出错，出错代码为{}".format(err))
        return char_label,char_roi,img_name,top_offset,bottom_offset
    
    def detect_char(self,img,img_name,top_offset,bottom_offset):
        try:
            self.log_oper.add_log("Normal>>开始进行多行字符识别")
            image_size=self.char_model_param['image_size']
            score_threshold=self.char_model_param['score_threshold']
            classes=self.char_model_param['classes']
            colors=self.char_model_param['colors']
            src_img = img.copy()
            img = img[:, :, ::-1]
            img_h, img_w = img.shape[:2]
            img_norm, scale = preprocess_image(img, image_size=image_size)
            boxes, scores, labels = self.char_model.predict_on_batch([np.expand_dims(img_norm, axis=0)])
            boxes, scores, labels = np.squeeze(boxes), np.squeeze(scores), np.squeeze(labels)                                
            boxes = postprocess_boxes(boxes=boxes, scale=scale, height=img_h, width=img_w)

            indices = np.where(scores[:] > score_threshold)[0]
            boxes = boxes[indices]
            labels = labels[indices]
            scores = scores[indices]

            res_nms = nms(boxes, scores, 0.1)
            boxes = boxes[res_nms]
            labels = labels[res_nms]
            scores = scores[res_nms]
            draw_boxes(src_img, boxes, scores, labels, colors, classes)

            #整理字符
            steel_no,steel_no_score,steel_type,steel_size=get_steel_info(boxes, scores, labels, classes)
            #cv2.imshow("ss",src_img)
            #cv2.waitKey()
            #input(steel_no)
            steel_no=steel_no.replace("B","8")
            steel_no=steel_no.replace("D","0")
            steel_no=steel_no.replace("I","1")
            steel_no=steel_no.replace("O","0")
            steel_no=steel_no.replace("S","5")

            exist_char=True
            if len(steel_no) != 14:
                self.log_oper.add_log("Warning>>当前识别钢板号{}不符合规则，放弃发送({})".format(steel_no,img_name))
                exist_char=False
            if False==steel_no.isdigit():
                self.log_oper.add_log("Warning>>当前识别钢板号{}未全部由数字组成，放弃发送({})".format(steel_no,img_name))
                exist_char=False
            if exist_char is True:
                self.cache_char.append([steel_no,steel_no_score,steel_type,steel_size,src_img,img,top_offset,bottom_offset,img_name])
                self.log_oper.add_log("Normal>>完成多行字符{}的识别，识别板号为：{}".format(img_name,steel_no))
        except Exception as err:
            self.log_oper.add_log("Error>>多行识别字符过程中出现错误，错误代码为{}".format(err))
            
    def detect_char_mini(self,img,img_name,top_offset,bottom_offset):
        try:
            self.log_oper.add_log("Normal>>开始进行单行字符识别")
            image_size=self.char_model_param_mini['image_size']
            score_threshold=self.char_model_param_mini['score_threshold']
            classes=self.char_model_param_mini['classes']
            colors=self.char_model_param_mini['colors']
            src_img = img.copy()
            img = img[:, :, ::-1]
            img_h, img_w = img.shape[:2]
            img_norm, scale = preprocess_image(img, image_size=image_size)
            boxes, scores, labels = self.char_model_mini.predict_on_batch([np.expand_dims(img_norm, axis=0)])
            boxes, scores, labels = np.squeeze(boxes), np.squeeze(scores), np.squeeze(labels)                                
            boxes = postprocess_boxes(boxes=boxes, scale=scale, height=img_h, width=img_w)

            indices = np.where(scores[:] > score_threshold)[0]
            boxes = boxes[indices]
            labels = labels[indices]
            scores = scores[indices]

            res_nms = nms(boxes, scores, 0.1)
            boxes = boxes[res_nms]
            labels = labels[res_nms]
            scores = scores[res_nms]
            draw_boxes(src_img, boxes, scores, labels, colors, classes)

            #整理字符
            steel_no,steel_no_score=get_steel_info_mini(boxes, scores, labels, classes)
            #cv2.imshow("ss",src_img)
            #cv2.waitKey()
            #input(steel_no)
            steel_no=steel_no.replace("B","8")
            steel_no=steel_no.replace("D","0")
            steel_no=steel_no.replace("I","1")
            steel_no=steel_no.replace("O","0")
            steel_no=steel_no.replace("S","5")

            exist_char=True
            if len(steel_no) != 14:
                self.log_oper.add_log("Warning>>当前识别钢板号{}不符合规则，放弃发送({})".format(steel_no,img_name))
                exist_char=False
            if False==steel_no.isdigit():
                self.log_oper.add_log("Warning>>当前识别钢板号{}未全部由数字组成，放弃发送({})".format(steel_no,img_name))
                exist_char=False
            if exist_char is True:
                self.cache_char.append([steel_no,steel_no_score,"","",src_img,img,top_offset,bottom_offset,img_name])
                self.log_oper.add_log("Normal>>完成单行字符{}的识别，识别板号为：{}".format(img_name,steel_no))
        except Exception as err:
            self.log_oper.add_log("Error>>单行识别字符过程中出现错误，错误代码为{}".format(err))
            
    def get_send_char(self,char_roi,cache_limit=True):
        try:
            #缓存字符统一处理
            steel_no,steel_type,steel_size,img_path=None,None,None,None
            if len(self.cache_char)<=0:
                return steel_no,steel_type,steel_size,img_path
            if cache_limit is True:
                if char_roi is not None and self.cache_num_index<self.max_cache_num:
                    return steel_no,steel_type,steel_size,img_path

            self.cache_char.sort(key=itemgetter(1), reverse=True)
            steel_no,steel_no_score,steel_type,steel_size,src_char_roi,char_roi,top_offset,bottom_offset,img_name=self.cache_char[0]
            self.cache_num_index=0
            self.cache_char=[]
            
            if self.last_steel_no==steel_no:
                self.log_oper.add_log("Normal>>当前识别钢板号{}已发送过，无需再次发送({})".format(steel_no,img_name))
                steel_no,steel_type,steel_size,img_path=None,None,None,None
                return steel_no,steel_type,steel_size,img_path
            #self.last_steel_no=steel_no

            #保存带标签的图片到本地
            char_roi_h, char_roi_w = char_roi.shape[:2]
            src_char_roi_cut=src_char_roi[max(int(0+top_offset)-10,0):min(int(char_roi_h-bottom_offset)+50,char_roi_h),:]
            save_char_img_path = os.path.join(self.path_char,img_name)
            cv2.imwrite(save_char_img_path,src_char_roi_cut)
            self.log_oper.add_log("Normal>>成功保存字符识别效果图")

            #保存字符图片到二级发送文件夹
            char_roi_cut_resize=cv2.resize(char_roi,(char_roi.shape[1],int(char_roi.shape[1]*0.75)))
            datetime=time.strftime("%Y%m%d")
            path_char_l2_curr = ((self.path_char_l2 + "\%s") % datetime)
            if not os.path.exists(path_char_l2_curr):
                os.mkdir(path_char_l2_curr)
            save_l2_char_img_path = os.path.join(path_char_l2_curr,img_name)
            cv2.imwrite(save_l2_char_img_path,char_roi_cut_resize)
            self.log_oper.add_log("Normal>>成功保存字符到二级文件夹")

            #保存样本
            save_sample_path = ((self.path_camera + "\%s") % datetime)
            if not os.path.exists(save_sample_path):
                os.mkdir(save_sample_path)
            save_sample_path_name = os.path.join(save_sample_path,img_name)
            save_steel_path = ((self.path_steel + "\%s") % datetime)
            save_img_path_name = os.path.join(save_steel_path,img_name)
            if os.path.exists(save_img_path_name):
                copyfile(save_img_path_name,save_sample_path_name)

            img_path=os.path.join(datetime,img_name)
            return steel_no,steel_type,steel_size,img_path
        except Exception as err:
            self.log_oper.add_log("Error>>整理字符过程中出现错误，错误代码为{}".format(err))
            steel_no,steel_type,steel_size,img_path=None,None,None,None
            return steel_no,steel_type,steel_size,img_path
        
    def send_char_to_l2(self,steel_no,steel_type,steel_size,img_path):
        self.counter=self.counter+1
        if self.counter>30000:
            self.counter=1
        send_to_l2(self.sock,self.log_oper,steel_no,steel_type,steel_size,img_path,self.counter,self.mark)
        self.log_oper.add_log("Normal>>识别字符发送到二级")
        self.last_steel_no=steel_no

    def send_char_to_l2_not_steel_no(self):
        self.counter=self.counter+1
        if self.counter>30000:
            self.counter=1
        #保存字符图片到二级发送文件夹
        img_name,char_roi_cut=self.curr_char_img_info[0],self.curr_char_img_info[1]
        char_roi_cut_resize=cv2.resize(char_roi_cut,(char_roi_cut.shape[1],int(char_roi_cut.shape[1]*0.75)))
        datetime=time.strftime("%Y%m%d")
        path_char_l2_curr = ((self.path_char_l2 + "\%s") % datetime)
        if not os.path.exists(path_char_l2_curr):
            os.mkdir(path_char_l2_curr)
        save_l2_char_img_path = os.path.join(path_char_l2_curr,img_name)
        cv2.imwrite(save_l2_char_img_path,char_roi_cut_resize)
        img_path=os.path.join(datetime,img_name)
        self.log_oper.add_log("Normal>>成功保存未识别字符到二级文件夹")
        
        send_to_l2(self.sock,self.log_oper,"None","","",img_path,self.counter,self.mark)
        self.log_oper.add_log("Normal>>未识别字符发送到二级")
        self.curr_char_img_info=[None,None]

    def send_char_to_l2_not_img(self):
        self.counter=self.counter+1
        if self.counter>30000:
            self.counter=1
        send_to_l2(self.sock,self.log_oper,"Error","","","",self.counter,self.mark)
        self.log_oper.add_log("Normal>>无识别字符发送到二级")
    


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
        score_threshold = 0.5
        colors = [np.random.randint(0, 256, 3).tolist() for _ in range(num_classes)]
        _, char_model = efficientdet(phi=phi,weighted_bifpn=weighted_bifpn,num_classes=num_classes,score_threshold=score_threshold)
        char_model.load_weights(model_path, by_name=True)
        char_model_param={'image_size':image_size,'classes':classes,'score_threshold':score_threshold,'colors':colors}
    except Exception as err:
        Log_oper.add_log("Error>>执行中出现错误{},程序自动重启".format(err))
        os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')
    Log_oper.add_log("Normal>>完成载入识别模型成功")

    Log_oper.add_log("Normal>>开始载入mini识别模型")
    try:
        phi_mini = 2
        weighted_bifpn_mini = True
        model_path_mini = 'char_model_mini/char_model.h5'
        image_sizes_mini = (512, 640, 768, 896, 1024, 1280, 1408)
        image_size_mini = image_sizes_mini[phi_mini]
        classes_mini = {value['id']: value['name'] for value in json.load(open('char_model_mini/char_class.json', 'r')).values()}
        num_classes_mini = len(classes_mini)
        score_threshold_mini = 0.5
        colors_mini = [np.random.randint(0, 256, 3).tolist() for _ in range(num_classes_mini)]
        _, char_model_mini = efficientdet(phi=phi_mini,weighted_bifpn=weighted_bifpn_mini,num_classes=num_classes_mini,score_threshold=score_threshold_mini)
        char_model_mini.load_weights(model_path_mini, by_name=True)
        char_model_param_mini={'image_size':image_size_mini,'classes':classes_mini,'score_threshold':score_threshold_mini,'colors':colors_mini}
    except Exception as err:
        Log_oper.add_log("Error>>执行中出现错误{},程序自动重启".format(err))
        os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')
    Log_oper.add_log("Normal>>完成载入mini识别模型成功")
    
    Log_oper.add_log("Normal>>开始创建二级连接")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('191.168.162.192', 12001))
        send_heartbeat = threading.Thread(target=thread_send_heartbeat_to_l2,args=(s,Log_oper,))
        send_heartbeat.start()
        #recv_info = threading.Thread(target=thread_recv_info_from_l2,args=(s,Log_oper,))
        #recv_info.start()
        t_recv_info=HThreadRecvInfo((s,Log_oper,),"recv")       
        t_recv_info.start()
    except Exception as err:
        Log_oper.add_log("Error>>执行中出现错误{},程序自动重启".format(err))
        os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')
    Log_oper.add_log("Normal>>完成成功连接到二级")

    judge_num_sbm=0
    SCD_SBM_Oper=SteelCharDetect(1,Log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,s,10,path_1)
    judge_num_htf1=0
    SCD_HTF1_Oper=SteelCharDetect(2,Log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,s,10,path_2)
    judge_num_htf2=0
    SCD_HTF2_Oper=SteelCharDetect(3,Log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,s,10,path_3)
    judge_num_print=0
    SCD_PRINT_Oper=SteelCharDetect(4,Log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,s,10,path_4)
    
    steel_no_send={"SBM":False,"HTF1":False,"HTF2":False,"PRINT":False}#根据一级信号判断钢板是否经过
    last_recv_res={"SBM":[1,1,1],"HTF1":[1,1,1],"HTF2":[1,1,1],"PRINT":[1,1,1]}
    char_roi=None
    enable_l2_final_send={"SBM":False,"HTF1":False,"HTF2":False,"PRINT":False} #程序重启后钢板不在识别区时不发送数据
    #第一位：二级是否搜到计划 1为未搜到 0为搜到 第二位：钢板是否在识别区 1为在识别区 0为不在识别区 第三位：辊道转速情况 1为正转 0为停止 -1为倒转 
    while True:
        Log_oper.add_log("Normal>>获得文件夹图像路径列表")
        time.sleep(1)
        

        Log_oper.add_log("Normal>>-----------------抛丸机前字符识别-----------------")
        #recv_res=t_recv_info.get_result()
        #print(recv_res)
        for root,dirs,files in os.walk(path_1["path_ref"]):
            img_path_list=[]
            
            if len(files)>0:                                                        #确定是否钢板已走完
                judge_num_sbm=0
            else:
                judge_num_sbm=judge_num_sbm+1
            num=0
            for file in files:
                if os.path.splitext(file)[1]=='.jpg':
                    num=num+1
                    if num>10:
                        break
                    img_path_list.append(os.path.join(path_1["path_ref"],file))
                    char_label,char_roi,img_name,top_offset,bottom_offset=SCD_SBM_Oper.detect_steel(file)
                    if char_roi is not None:
                        if char_label != 'tchar':
                            SCD_SBM_Oper.detect_char(char_roi,img_name,top_offset,bottom_offset)
                        else:
                            SCD_SBM_Oper.detect_char_mini(char_roi,img_name,top_offset,bottom_offset)
                    steel_no,steel_type,steel_size,img_path=SCD_SBM_Oper.get_send_char(char_roi,cache_limit=True)
                    if steel_no is not None:
                        recv_res=t_recv_info.get_result()
                        if recv_res["SBM"][0]==1 and recv_res["SBM"][2]>=0:  #还未依据钢板号查到计划且辊道速度不为负
                            SCD_SBM_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)
                            steel_no_send["SBM"]=True

            recv_res=t_recv_info.get_result()                                   #一级状态
            if recv_res["SBM"][1]==1:
                enable_l2_final_send["SBM"]=True
            if recv_res["SBM"][1]==0 and last_recv_res["SBM"][1]==1:
                if recv_res["SBM"][2]>=0 and enable_l2_final_send["SBM"] is True:
                    if steel_no_send["SBM"] is not True:
                        steel_no,steel_type,steel_size,img_path=SCD_SBM_Oper.get_send_char(char_roi,cache_limit=True)
                        if steel_no is not None:
                            SCD_SBM_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)
                        else:
                            if SCD_SBM_Oper.curr_char_img_info[1] is not None:
                                SCD_SBM_Oper.send_char_to_l2_not_steel_no()
                            else:
                                SCD_SBM_Oper.send_char_to_l2_not_img()
            elif recv_res["SBM"][1]==1 and last_recv_res["SBM"][1]==0:
                steel_no_send["SBM"]=False
                SCD_SBM_Oper.last_steel_no="00000000000000"                         #钢板重新进入后，上一次发送的板号置0
                SCD_SBM_Oper.curr_char_img_info=[None,None]
            last_recv_res["SBM"]=copy.deepcopy(recv_res["SBM"])
                       
            if judge_num_sbm>5:                                                     #如果连续五次搜索不到图像需要确认缓存中是否还存在字符 
                steel_no,steel_type,steel_size,img_path=SCD_SBM_Oper.get_send_char(char_roi,cache_limit=False)
                if steel_no is not None:
                    SCD_SBM_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)
            delete_file(Log_oper,img_path_list)

        Log_oper.add_log("Normal>>-----------------一号加热炉前字符识别-----------------")
        for root,dirs,files in os.walk(path_2["path_ref"]):
            img_path_list=[]
            
            if len(files)>0:                                                        #确定是否钢板已走完
                judge_num_htf1=0
            else:
                judge_num_htf1=judge_num_htf1+1
            num=0
            for file in files:
                if os.path.splitext(file)[1]=='.jpg':
                    num=num+1
                    if num>10:
                        break
                    img_path_list.append(os.path.join(path_2["path_ref"],file))
                    char_label,char_roi,img_name,top_offset,bottom_offset=SCD_HTF1_Oper.detect_steel(file)
                    if char_roi is not None:
                        if char_label != 'tchar':
                            SCD_HTF1_Oper.detect_char(char_roi,img_name,top_offset,bottom_offset)
                        else:
                            SCD_HTF1_Oper.detect_char_mini(char_roi,img_name,top_offset,bottom_offset)
                    steel_no,steel_type,steel_size,img_path=SCD_HTF1_Oper.get_send_char(char_roi,cache_limit=True)
                    if steel_no is not None:
                        SCD_HTF1_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)
            
            if judge_num_htf1<5:                                                    #如果连续五次搜索不到图像需要确认缓存中是否还存在字符 
                steel_no,steel_type,steel_size,img_path=SCD_HTF1_Oper.get_send_char(char_roi,cache_limit=False)
                if steel_no is not None:
                    SCD_HTF1_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)
            delete_file(Log_oper,img_path_list)

        Log_oper.add_log("Normal>>-----------------二号加热炉前字符识别-----------------")
        for root,dirs,files in os.walk(path_3["path_ref"]):
            img_path_list=[]           
            if len(files)>0:                                                        #确定是否钢板已走完
                judge_num_htf2=0
            else:
                judge_num_htf2=judge_num_htf2+1
            num=0
            for file in files:
                if os.path.splitext(file)[1]=='.jpg':
                    num=num+1
                    if num>10:
                        break
                    img_path_list.append(os.path.join(path_3["path_ref"],file))
                    char_label,char_roi,img_name,top_offset,bottom_offset=SCD_HTF2_Oper.detect_steel(file)
                    if char_roi is not None:
                        if char_label != 'tchar':
                            SCD_HTF2_Oper.detect_char(char_roi,img_name,top_offset,bottom_offset)
                        else:
                            SCD_HTF2_Oper.detect_char_mini(char_roi,img_name,top_offset,bottom_offset)
                    steel_no,steel_type,steel_size,img_path=SCD_HTF2_Oper.get_send_char(char_roi,cache_limit=True)
                    if steel_no is not None:
                        SCD_HTF2_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)            
            if judge_num_htf2<5:                                                    #如果连续五次搜索不到图像需要确认缓存中是否还存在字符
                steel_no,steel_type,steel_size,img_path=SCD_HTF2_Oper.get_send_char(char_roi,cache_limit=False)
                if steel_no is not None:
                    SCD_HTF2_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)
            delete_file(Log_oper,img_path_list)

        Log_oper.add_log("Normal>>-----------------喷印前字符识别-----------------")
        for root,dirs,files in os.walk(path_4["path_ref"]):
            img_path_list=[]
            
            if len(files)>0:                                                        #确定是否钢板已走完
                judge_num_print=0
            else:
                judge_num_print=judge_num_print+1
            num=0
            for file in files:
                if os.path.splitext(file)[1]=='.jpg':
                    num=num+1
                    if num>10:
                        break
                    img_path_list.append(os.path.join(path_4["path_ref"],file))
                    char_label,char_roi,img_name,top_offset,bottom_offset=SCD_PRINT_Oper.detect_steel(file)
                    if char_roi is not None:
                        if char_label != 'tchar':
                            SCD_PRINT_Oper.detect_char(char_roi,img_name,top_offset,bottom_offset)
                        else:
                            SCD_PRINT_Oper.detect_char_mini(char_roi,img_name,top_offset,bottom_offset)
                    steel_no,steel_type,steel_size,img_path=SCD_PRINT_Oper.get_send_char(char_roi,cache_limit=True)
                    if steel_no is not None:
                        SCD_PRINT_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)
             
            if judge_num_print<5:                                                   #如果连续五次搜索不到图像需要确认缓存中是否还存在字符
                steel_no,steel_type,steel_size,img_path=SCD_PRINT_Oper.get_send_char(char_roi,cache_limit=False)
                if steel_no is not None:
                    SCD_PRINT_Oper.send_char_to_l2(steel_no,steel_type,steel_size,img_path)
            delete_file(Log_oper,img_path_list)

            
    steel_model.close_session()
