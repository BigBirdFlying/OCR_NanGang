import os
import time
import math
import cv2
import json
import copy
import socket
import threading
import queue
import glob
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
from hkj_ibkvision_char.hkj_char_oper import get_steel_info,get_steel_info_mini,cal_iou
from hkj_ibkvision_char.hkj_signal_oper import send_to_l2,thread_send_heartbeat_to_l2,HThreadRecvInfo
from hkj_ibkvision_char.steel_unit.yolo import YOLO
from hkj_ibkvision_char.char_unit.model import efficientdet
from hkj_ibkvision_char.char_unit.init import preprocess_image, postprocess_boxes, preprocess_image_char,postprocess_boxes_char
from hkj_ibkvision_char.char_unit.draw_boxes import draw_boxes,nms
from hkj_ibkvision_char.hkj_char_classifier import get_convert_from_class_table,get_convert_from_ini_config_file,Classifier

image_cache_cam1 = queue.Queue(maxsize = 100)
image_cache_cam2 = queue.Queue(maxsize = 100)
image_cache_cam3 = queue.Queue(maxsize = 100)
image_cache_cam4 = queue.Queue(maxsize = 100)

def thread_load_camimg1(log_oper,path):
    while True:
        try:
            for root,dirs,files in os.walk(path["path_ref"]):
                if len(files)>0:
                    img_path_list=[]
                    time.sleep(0.5)
                    for file in files:
                        if os.path.splitext(file)[1]=='.jpg':                
                            if os.path.exists(os.path.join(path["path_ref"],file)):
                                img_info={}
                                img_info["img_path"]=os.path.join(path["path_ref"],file)
                                img_info["img_name"]=file
                                img_info['img_data']=cv2.imread(img_info["img_path"], 0)
                                if img_info['img_data'] is None:
                                    continue
                                image_cache_cam1.put(img_info)
                                img_path_list.append(img_info["img_path"])
                    delete_file(log_oper,img_path_list)
                else:
                    time.sleep(0.1)
        except Exception as err:
            log_oper.add_log("Error>>相机1图像载入线程中Bug->{}".format(err))
            continue

def thread_load_camimg2(log_oper,path):
    while True:
        try:
            for root,dirs,files in os.walk(path["path_ref"]):
                if len(files)>0:
                    img_path_list=[]
                    time.sleep(0.5)
                    for file in files:
                        if os.path.splitext(file)[1]=='.jpg':
                            if os.path.exists(os.path.join(path["path_ref"],file)):
                                img_info={}
                                img_info["img_path"]=os.path.join(path["path_ref"],file)
                                img_info["img_name"]=file
                                img_info['img_data']=cv2.imread(img_info["img_path"], 0)
                                if img_info['img_data'] is None:
                                    continue
                                image_cache_cam2.put(img_info)
                                img_path_list.append(img_info["img_path"])
                    delete_file(log_oper,img_path_list)
                else:
                    time.sleep(0.1)
        except Exception as err:
            log_oper.add_log("Error>>相机2图像载入线程中Bug->{}".format(err))
            continue

def thread_load_camimg3(log_oper,path):
    while True:
        try:
            for root,dirs,files in os.walk(path["path_ref"]):
                if len(files)>0:
                    img_path_list=[]
                    time.sleep(0.5)
                    for file in files:
                        if os.path.splitext(file)[1]=='.jpg':                            
                            if os.path.exists(os.path.join(path["path_ref"],file)):                                
                                img_info={}
                                img_info["img_path"]=os.path.join(path["path_ref"],file)
                                img_info["img_name"]=file
                                img_info['img_data']=cv2.imread(img_info["img_path"], 0)
                                if img_info['img_data'] is None:
                                    continue
                                image_cache_cam3.put(img_info)
                                img_path_list.append(img_info["img_path"])
                    delete_file(log_oper,img_path_list)
                else:
                    time.sleep(0.1)
        except Exception as err:
            log_oper.add_log("Error>>相机3图像载入线程中Bug->{}".format(err))
            continue

def thread_load_camimg4(log_oper,path):
    while True:
        try:
            for root,dirs,files in os.walk(path["path_ref"]):
                if len(files)>0:
                    img_path_list=[]
                    time.sleep(0.5)
                    for file in files:
                        if os.path.splitext(file)[1]=='.jpg':                           
                            if os.path.exists(os.path.join(path["path_ref"],file)):                               
                                img_info={}
                                img_info["img_path"]=os.path.join(path["path_ref"],file)
                                img_info["img_name"]=file
                                img_info['img_data']=cv2.imread(img_info["img_path"], 0)
                                if img_info['img_data'] is None:
                                    continue
                                image_cache_cam4.put(img_info)
                                img_path_list.append(img_info["img_path"])
                    delete_file(log_oper,img_path_list)
                else:
                    time.sleep(0.1)
        except Exception as err:
            log_oper.add_log("Error>>相机4图像载入线程中Bug->{}".format(err))
            continue            

class SteelCharDetect:
    
    def __init__(self,mark,log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,char_model_number,char_model_param_number,sock,max_cache_num,path):
        self.mark=mark
        self.log_oper=log_oper
        self.steel_model=steel_model
        self.char_model=char_model
        self.char_model_param=char_model_param
        self.char_model_mini=char_model_mini
        self.char_model_param_mini=char_model_param_mini
        self.char_model_number=char_model_number
        self.char_model_param_number=char_model_param_number
        self.sock=sock
        self.max_cache_num=max_cache_num
        self.path_camera=path["path_camera"]
        self.path_ref=path["path_ref"]
        self.path_steel=path["path_steel"]
        self.path_char=path["path_char"]
        self.path_char_l2=path["path_char_l2"]
        self.is_save_exists_char_img=True
        self.is_save_idenfiy_char_img=True
        self.cache_num_index=0
        self.cache_char=[]
        self.curr_idfy_img_info={"img_name":None,"char_roi":None,"src_img":None}
        self.curr_char_img_info={"img_name":None,"char_roi":None,"src_img":None}#识别为None时的图像
        self.curr_steel_img_info={"img_name":None,"char_roi":None,"src_img":None}#识别为Error时的图像
        self.last_steel_no="00000000000000"
        self.counter=0
        
    def image_map(self,img,left_top,right_top,right_bottom,left_bottom):
        img_h,img_w=img.shape[0:2]
        pts1=np.float32([left_top,right_top,right_bottom,left_bottom])
        pts2=np.float32([[0,0],[img_w,0],[img_w,img_h],[0,img_h]])
        M=cv2.getPerspectiveTransform(pts1,pts2)
        img=cv2.warpPerspective(img,M,(img_w,img_h))
        return img
        
    def detect_steel(self,img_path,img_name,img_data):
        char_roi=None
        char_label=''
        top_offset,bottom_offset=0,0
        try:
            self.log_oper.add_log("Normal>>开始检测{}的图像是否存在字符".format(img_path))
            start = time.time()
            #img_data_color=cv2.cvtColor(img_data,cv2.COLOR_GRAY2BGR)
            #src_image_Image = Image.fromarray(img_data.astype(np.uint8))
            src_image_Image = Image.fromarray(img_data)
            src_image_Image = src_image_Image.convert("RGB")
            src_image_Opencv=cv2.cvtColor(img_data,cv2.COLOR_GRAY2RGB)
            src_image_width,src_image_height=src_image_Image.size[0],src_image_Image.size[1]
            self.curr_steel_img_info={"img_name":img_name,"char_roi":None,"src_img":src_image_Opencv}
        except Exception as err:
            self.log_oper.add_log("Error>>文件打开错误，直接跳过，错误代码为{}".format(err))
        else:
            try:
                r_image,result = self.steel_model.detect_image(src_image_Image)
                max_area=0
                result_more = None
                if len(result) > 0:
                    result.sort(key=lambda i: i['score'], reverse=True)
                    result_more = copy.deepcopy(result[0])
                    for n in range(0, len(result)):
                        (top, left, bottom, right) = result[n]['box']
                        roi_a = (right - left) * (bottom - top)
                        (top_more, left_more, bottom_more, right_more) = result_more['box']
                        roi_a_more = (right_more - left_more) * (bottom_more - top_more)
                        fe = cal_iou(result[n]['box'], result_more['box'])
                        if roi_a > roi_a_more and fe < 0.1:
                            result_more = copy.deepcopy(result[n])

                    (top, left, bottom, right) = result_more['box']
                    to_top=top-0
                    to_bottom=src_image_height-bottom
                    to_left=left-0
                    to_right=src_image_width-right
                    roi_w=right-left
                    roi_h=bottom-top
                    roi_a=roi_w*roi_h
                    
                    if roi_w>src_image_width*0.1 and to_left>src_image_width*0.1 and to_right>src_image_width*0.1 and to_top>=0 and to_bottom>=0:
                        #限制多少缓存字符后发送
                        self.cache_num_index=self.cache_num_index+1
                        #存在字符则进行存储
                        '''
                        if self.is_save_exists_char_img is True:
                            datetime=time.strftime("%Y%m%d")
                            save_img_path = ((self.path_steel + "\%s") % datetime)
                            if not os.path.exists(save_img_path):
                                os.mkdir(save_img_path)
                            save_img_path_name = os.path.join(save_img_path,img_name)
                            cv2.imwrite(save_img_path_name,src_image_Opencv)
                            self.log_oper.add_log("Normal>>图像上存在字符，图像保存")
                        '''
                        #判断字符是否为倒置
                        if result_more['class']=='unchar':
                            src_image_Opencv=rotate_bound(src_image_Opencv,180)
                            top,bottom=src_image_height-bottom,src_image_height-top
                            left,right=src_image_width-right,src_image_width-left
                            self.log_oper.add_log("Normal>>检测到字符为倒置状态，进行翻转")

                        #拓展图像
                        if result_more['class']=='unchar' or result_more['class']=='char':
                            left=max(0,left-0)
                            right=min(src_image_width,right+0)
                        else:
                            left=max(0,left-50)
                            right=min(src_image_width,right+50)
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
                            char_label=result_more['class']
                            if self.curr_char_img_info["char_roi"] is None:
                                self.curr_char_img_info={"img_name":img_name,"char_roi":char_roi,"src_img":src_image_Opencv}
                            else:
                                roi_area=char_roi.shape[0]*char_roi.shape[1]
                                cur_area=self.curr_char_img_info["char_roi"].shape[0]*self.curr_char_img_info["char_roi"].shape[1]
                                if roi_area>cur_area:
                                    self.curr_char_img_info={"img_name":img_name,"char_roi":char_roi,"src_img":src_image_Opencv}
                            self.log_oper.add_log("Normal>>成功获得字符ROI")
                end = time.time()
                self.log_oper.add_log("Normal>>完成检测{}的图像是否存在字符，共用时{}秒".format(img_path,end-start))
            except Exception as err:
                self.log_oper.add_log("Error>>识别钢板是否存在字符出错，出错代码为{}".format(err))
        return char_label,char_roi,top_offset,bottom_offset
    
    def detect_char(self,img,src_img,img_name,top_offset,bottom_offset):
        try:
            self.log_oper.add_log("Normal>>开始进行多行字符识别")
            image_size=self.char_model_param['image_size']
            score_threshold=self.char_model_param['score_threshold']
            classes=self.char_model_param['classes']
            colors=self.char_model_param['colors']
            res_img = img.copy()
            char_roi = img.copy()
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
            draw_boxes(res_img, boxes, scores, labels, colors, classes)

            #整理字符
            steel_no,steel_no_score,steel_type,steel_size,steel_no_boxes=get_steel_info(boxes, scores, labels, classes)

            steel_no=steel_no.replace("B","8")
            steel_no=steel_no.replace("D","0")
            steel_no=steel_no.replace("I","1")
            steel_no=steel_no.replace("O","0")
            steel_no=steel_no.replace("S","5")
            steel_no=steel_no.replace("Z","2")

            exist_char=True
            if len(steel_no) != 14:
                self.log_oper.add_log("Warning>>当前识别钢板号{}不符合规则，放弃发送({})".format(steel_no,img_name))
                exist_char=False
            if False==steel_no.isdigit():
                self.log_oper.add_log("Warning>>当前识别钢板号{}未全部由数字组成，放弃发送({})".format(steel_no,img_name))
                exist_char=False
            if exist_char is True:
                #进行钢板号二次分类
                char_w,char_h=0,0
                char_x_min,char_x_max=99999,0
                char_y_min,char_y_max=99999,0
                img_mini_list=[]
                for i in range(0,len(steel_no_boxes)):
                    box=steel_no_boxes[i]
                    xmin, ymin, xmax, ymax = box
                    char_w=char_w+(xmax-xmin)
                    char_h=char_h+(ymax-ymin)
                    if xmin<char_x_min:
                        char_x_min=xmin
                    if ymin<char_y_min:
                        char_y_min=ymin
                    if xmax>char_x_max:
                        char_x_max=xmax 
                    if ymax>char_y_max:
                        char_y_max=ymax 
                    img_mini=img[int(ymin):int(ymax),int(xmin):int(xmax)]
                
                #进行纯数字检测
                steel_number_img=self.get_only_steelno_img(steel_no_boxes,img)
                final_steelno,final_steelno_score=self.get_final_steelno(steel_number_img)
                if final_steelno is not None:
                    self.log_oper.add_log("Normal>>多行原钢板号识别为：{}，更正识别板号为：{}".format(steel_no,final_steelno))
                    steel_no=final_steelno
                    steel_no_score=final_steelno_score

                #发送二级的图上写字符
                if len(steel_no_boxes)>0:
                    char_w=char_w/len(steel_no_boxes)
                    char_h=char_h/len(steel_no_boxes)
                cv2.rectangle(char_roi, (max(0,int(char_x_min-char_w*0.2)), max(0,int(char_y_min-char_h*2))),
                                        (min(img_w,int(char_x_max+char_w*0.2)), min(img_h,int(char_y_max-char_h*2))), (0,255,255), 3)#2
                for i in range(0,len(steel_no_boxes)):
                    box=steel_no_boxes[i]
                    xmin, ymin, xmax, ymax = box
                    cv2.putText(char_roi, str(list(steel_no)[i]), (int(xmin), int(char_y_min - char_h)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                #
                self.cache_char.append([steel_no,steel_no_score,steel_type,steel_size,char_roi,src_img,res_img,top_offset,bottom_offset,img_name])
                self.log_oper.add_log("Normal>>完成多行字符{}的识别，识别板号为：{}".format(img_name,steel_no))
        except Exception as err:
            self.log_oper.add_log("Error>>多行识别字符过程中出现错误，错误代码为{}".format(err))
            
    def detect_char_mini(self,img,src_img,img_name,top_offset,bottom_offset):
        try:
            self.log_oper.add_log("Normal>>开始进行单行字符识别")
            image_size=self.char_model_param_mini['image_size']
            score_threshold=self.char_model_param_mini['score_threshold']
            classes=self.char_model_param_mini['classes']
            colors=self.char_model_param_mini['colors']
            res_img = img.copy()
            char_roi = img.copy()
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
            draw_boxes(res_img, boxes, scores, labels, colors, classes)

            #整理字符
            steel_no,steel_no_score,steel_no_boxes=get_steel_info_mini(boxes, scores, labels, classes)

            steel_no=steel_no.replace("B","8")
            steel_no=steel_no.replace("D","0")
            steel_no=steel_no.replace("I","1")
            steel_no=steel_no.replace("O","0")
            steel_no=steel_no.replace("S","5")
            steel_no=steel_no.replace("Z","2")

            exist_char=True
            if len(steel_no) != 14:
                self.log_oper.add_log("Warning>>当前识别钢板号{}不符合规则，放弃发送({})".format(steel_no,img_name))
                exist_char=False
            if False==steel_no.isdigit():
                self.log_oper.add_log("Warning>>当前识别钢板号{}未全部由数字组成，放弃发送({})".format(steel_no,img_name))
                exist_char=False
            if exist_char is True:
                #进行钢板号二次分类
                char_w,char_h=0,0
                char_x_min,char_x_max=99999,0
                char_y_min,char_y_max=99999,0
                img_mini_list=[]
                for i in range(0,len(steel_no_boxes)):
                    box=steel_no_boxes[i]
                    xmin, ymin, xmax, ymax = box
                    char_w=char_w+(xmax-xmin)
                    char_h=char_h+(ymax-ymin)
                    if xmin<char_x_min:
                        char_x_min=xmin
                    if ymin<char_y_min:
                        char_y_min=ymin
                    if xmax>char_x_max:
                        char_x_max=xmax 
                    if ymax>char_y_max:
                        char_y_max=ymax 
                    img_mini=img[int(ymin):int(ymax),int(xmin):int(xmax)]
                    img_mini_list.append(img_mini)
                    
                #进行纯数字检测
                steel_number_img=self.get_only_steelno_img(steel_no_boxes,img)
                final_steelno,final_steelno_score=self.get_final_steelno(steel_number_img)
                if final_steelno is not None:
                    self.log_oper.add_log("Normal>>单行原钢板号识别为：{}，更正识别板号为：{}".format(steel_no,final_steelno))
                    steel_no=final_steelno
                    steel_no_score=final_steelno_score
                

                #发送二级的图上写字符
                if len(steel_no_boxes)>0:
                    char_w=char_w/len(steel_no_boxes)
                    char_h=char_h/len(steel_no_boxes)
                cv2.rectangle(char_roi, (max(0,int(char_x_min-char_w*0.2)), max(0,int(char_y_min-char_h*2))),
                                        (min(img_w,int(char_x_max+char_w*0.2)), min(img_h,int(char_y_max-char_h*2))), (0,255,255), 3)#2
                for i in range(0,len(steel_no_boxes)):
                    box=steel_no_boxes[i]
                    xmin, ymin, xmax, ymax = box
                    cv2.putText(char_roi, str(list(steel_no)[i]), (int(xmin), int(max(0,char_y_min - char_h))), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                #
                self.cache_char.append([steel_no,steel_no_score,"","",char_roi,src_img,res_img,top_offset,bottom_offset,img_name])
                self.log_oper.add_log("Normal>>完成单行字符{}的识别，识别板号为：{}".format(img_name,steel_no))
        except Exception as err:
            self.log_oper.add_log("Error>>单行识别字符过程中出现错误，错误代码为{}".format(err))
    
    def get_only_steelno_img(self,steel_no_boxes,img):
        img_h, img_w = img.shape[:2]
    
        char_w,char_h=0,0
        char_x_min,char_x_max=99999,0
        char_y_min,char_y_max=99999,0
        img_mini_list=[]               
        for i in range(0,len(steel_no_boxes)):
            box=steel_no_boxes[i]
            xmin, ymin, xmax, ymax = box
            char_w=char_w+(xmax-xmin)
            char_h=char_h+(ymax-ymin)
            if xmin<char_x_min:
                char_x_min=xmin
            if ymin<char_y_min:
                char_y_min=ymin
            if xmax>char_x_max:
                char_x_max=xmax 
            if ymax>char_y_max:
                char_y_max=ymax 
            img_mini=img[int(ymin):int(ymax),int(xmin):int(xmax)]
            img_mini_list.append(img_mini)
        y1_y0=(steel_no_boxes[-1][3]+steel_no_boxes[-1][1])/2-(steel_no_boxes[0][3]+steel_no_boxes[0][1])/2
        x1_x0=(steel_no_boxes[-1][2]+steel_no_boxes[-1][0])/2-(steel_no_boxes[0][2]+steel_no_boxes[0][0])/2
        k=y1_y0/x1_x0
        angle = math.atan2(y1_y0, x1_x0)
        angle = int(angle * 180/math.pi)
        s_roi_xmin=max(int(char_x_min-char_w*0.2/len(steel_no_boxes)),0)
        s_roi_xmax=min(int(char_x_max+char_w*0.2/len(steel_no_boxes)),img_w)
        s_roi_ymin=int(char_y_min)
        s_roi_ymax=int(char_y_max)
        s_roi=img[s_roi_ymin:s_roi_ymax,s_roi_xmin:s_roi_xmax]
        ww=s_roi_xmax-s_roi_xmin
        hh=s_roi_ymax-s_roi_ymin
        res_steelno_img=np.ones((ww,ww,3),np.uint8)*155
        res_steelno_img[int((ww-hh)/2):int((ww-hh)/2)+hh,:,:]=s_roi
        #res=rotate_bound(res,-angle)
        return s_roi
        
    def get_final_steelno(self,img):
        image_size=self.char_model_param_number['image_size']
        score_threshold=self.char_model_param_number['score_threshold']
        classes=self.char_model_param_number['classes']
        colors=self.char_model_param_number['colors']
        src_img = img.copy()
        img = img[:, :, ::-1]
            
        img_h, img_w = img.shape[:2]
        img_norm, scale, left_offset,top_offset = preprocess_image_char(img, image_size=image_size)
        
        boxes, scores, labels = self.char_model_number.predict_on_batch([np.expand_dims(img_norm, axis=0)])
        boxes, scores, labels = np.squeeze(boxes), np.squeeze(scores), np.squeeze(labels)                                
        boxes = postprocess_boxes_char(boxes=boxes, scale=scale, height=img_h, width=img_w,left_offset=left_offset,top_offset=top_offset)

        indices = np.where(scores[:] > score_threshold)[0]
        boxes = boxes[indices]
        labels = labels[indices]
        scores = scores[indices]

        res_nms = nms(boxes, scores, 0.1)
        boxes = boxes[res_nms]
        labels = labels[res_nms]
        scores = scores[res_nms]
        
        draw_img=np.zeros((img_h*2,img_w,3),np.uint8)
        draw_img[0:img_h,:,:]=src_img
        draw_boxes(draw_img, boxes, scores, labels, colors, classes)
        
        char_boxs=[]
        for b, l, s in zip(boxes, labels, scores):
            class_id = int(l)
            score_id = float(s)
            xmin, ymin, xmax, ymax = list(map(int, b))
            temp_box=[xmin, ymin, xmax, ymax, classes[class_id],score_id]
            char_boxs.append(temp_box)
        char_boxs.sort(key=itemgetter(0), reverse=False)
        if len(char_boxs)==14:
            steel_no=''
            steel_no_score=0
            for i in range(0,len(char_boxs)):
                steel_no=steel_no+str(char_boxs[i][4])
                steel_no_score=steel_no_score+int(char_boxs[i][5])
            steel_no_score=steel_no_score/14
            return steel_no,steel_no_score
        else:
            return None,0
        
    def get_send_char(self,char_roi,cache_limit=True):
        try:
            #缓存字符统一处理
            steel_no,steel_type,steel_size=None,None,None
            if len(self.cache_char)<=0:
                return steel_no,steel_type,steel_size
            if cache_limit is True:
                if char_roi is not None and self.cache_num_index<self.max_cache_num:
                    return steel_no,steel_type,steel_size

            self.cache_char.sort(key=itemgetter(1), reverse=True)
            steel_no,steel_no_score,steel_type,steel_size,char_roi,src_img,res_img,top_offset,bottom_offset,img_name=self.cache_char[0]
            self.cache_num_index=0
            self.cache_char=[]
            
            if self.last_steel_no==steel_no:
                self.log_oper.add_log("Normal>>当前识别钢板号{}已发送过，无需再次发送({})".format(steel_no,img_name))
                steel_no,steel_type,steel_size=None,None,None
                return steel_no,steel_type,steel_size
            
            self.curr_idfy_img_info={"img_name":img_name,"char_roi":char_roi,"src_img":src_img}          
            return steel_no,steel_type,steel_size
        except Exception as err:
            self.log_oper.add_log("Error>>整理字符过程中出现错误，错误代码为{}".format(err))
            steel_no,steel_type,steel_size=None,None,None
            return steel_no,steel_type,steel_size
        
    def send_char_to_l2(self,steel_no,steel_type,steel_size):
        self.counter=self.counter+1
        if self.counter>30000:
            self.counter=1

        img_name,char_roi,src_img=self.curr_idfy_img_info["img_name"],self.curr_idfy_img_info["char_roi"],self.curr_idfy_img_info["src_img"]
        #保存字符图片到二级发送文件夹
        char_roi_resize=cv2.resize(char_roi,(char_roi.shape[1],int(char_roi.shape[1]*0.75)))
        datetime=time.strftime("%Y%m%d")
        path_char_l2_curr = ((self.path_char_l2 + "\%s") % datetime)
        if not os.path.exists(path_char_l2_curr):
            os.mkdir(path_char_l2_curr)
        save_l2_char_img_path = os.path.join(path_char_l2_curr,img_name)
        cv2.imwrite(save_l2_char_img_path,char_roi_resize)
        img_path=os.path.join(datetime,img_name)
        self.log_oper.add_log("Normal>>成功保存字符到二级文件夹")
        #保存样本到文件夹
        datetime=time.strftime("%Y%m%d")
        save_sample_path = ((self.path_camera + "\%s") % datetime)
        if not os.path.exists(save_sample_path):
            os.mkdir(save_sample_path)
        save_sample_path_name = os.path.join(save_sample_path,img_name)
        cv2.imwrite(save_sample_path_name,src_img) 
        #
        send_to_l2(self.sock,self.log_oper,steel_no,steel_type,steel_size,img_path,self.counter,self.mark)
        self.log_oper.add_log("Normal>>识别字符发送到二级")
        self.last_steel_no=steel_no

    def send_char_to_l2_not_steel_no(self):
        self.counter=self.counter+1
        if self.counter>30000:
            self.counter=1
        
        img_name,char_roi,src_img=self.curr_char_img_info["img_name"],self.curr_char_img_info["char_roi"],self.curr_char_img_info["src_img"]
        #保存字符图片到二级发送文件夹
        char_roi_resize=cv2.resize(char_roi,(char_roi.shape[1],int(char_roi.shape[1]*0.75)))
        datetime=time.strftime("%Y%m%d")
        path_char_l2_curr = ((self.path_char_l2 + "\%s") % datetime)
        if not os.path.exists(path_char_l2_curr):
            os.mkdir(path_char_l2_curr)
        save_l2_char_img_path = os.path.join(path_char_l2_curr,img_name)
        cv2.imwrite(save_l2_char_img_path,char_roi_resize)
        img_path=os.path.join(datetime,img_name)
        self.log_oper.add_log("Normal>>成功保存未识别字符到二级文件夹")
        #保存样本到文件夹
        datetime=time.strftime("%Y%m%d")
        save_sample_path = ((self.path_camera + "\%s") % datetime)
        if not os.path.exists(save_sample_path):
            os.mkdir(save_sample_path)
        save_sample_path_name = os.path.join(save_sample_path,img_name)
        cv2.imwrite(save_sample_path_name,src_img)      
        #
        send_to_l2(self.sock,self.log_oper,"None","","",img_path,self.counter,self.mark)
        self.log_oper.add_log("Normal>>未识别字符发送到二级")
        self.curr_char_img_info={"img_name":None,"char_roi":None,"src_img":None}

    def send_char_to_l2_not_img(self):
        self.counter=self.counter+1
        if self.counter>30000:
            self.counter=1
                    
        if self.curr_steel_img_info["src_img"] is not None:
            #保存字符图片到二级发送文件夹
            img_name,src_img=self.curr_steel_img_info["img_name"],self.curr_steel_img_info["src_img"]
            src_img_resize=cv2.resize(src_img,(src_img.shape[1],int(src_img.shape[1]*0.75)))
            datetime=time.strftime("%Y%m%d")
            path_steel_l2_curr = ((self.path_char_l2 + "\%s") % datetime)
            if not os.path.exists(path_steel_l2_curr):
                os.mkdir(path_steel_l2_curr)
            save_l2_steel_img_path = os.path.join(path_steel_l2_curr,img_name)
            cv2.imwrite(save_l2_steel_img_path,src_img_resize)
            img_path=os.path.join(datetime,img_name)
            self.log_oper.add_log("Normal>>成功保存无字符图像到二级文件夹")
            #
            send_to_l2(self.sock,self.log_oper,"Error","","",img_path,self.counter,self.mark)
        else:
            send_to_l2(self.sock,self.log_oper,"Error","","","",self.counter,self.mark)
            
        self.log_oper.add_log("Normal>>无识别字符发送到二级")
        self.curr_steel_img_info={"img_name":None,"char_roi":None,"src_img":None}


def init_delete_imgfile(log_oper,path_1,path_2,path_3,path_4):
    for root,dirs,files in os.walk(path_1["path_ref"]):
        img_path_list=[]
        for file in files:
            if os.path.splitext(file)[1]=='.jpg':
                img_path_list.append(os.path.join(path_1["path_ref"],file))
        delete_file(log_oper,img_path_list)
    #
    for root,dirs,files in os.walk(path_2["path_ref"]):
        img_path_list=[]
        for file in files:
            if os.path.splitext(file)[1]=='.jpg':
                img_path_list.append(os.path.join(path_2["path_ref"],file))
        delete_file(log_oper,img_path_list)
    #
    for root,dirs,files in os.walk(path_3["path_ref"]):
        img_path_list=[]
        for file in files:
            if os.path.splitext(file)[1]=='.jpg':
                img_path_list.append(os.path.join(path_3["path_ref"],file))
        delete_file(log_oper,img_path_list)
    #
    for root,dirs,files in os.walk(path_4["path_ref"]):
        img_path_list=[]
        for file in files:
            if os.path.splitext(file)[1]=='.jpg':
                img_path_list.append(os.path.join(path_4["path_ref"],file))
        delete_file(log_oper,img_path_list)

g_temp=False
g_temp_num=0
def steel_char_detect(path_1,path_2,path_3,path_4):
    try:
        Log_oper=Log("Log_ASC") 
        
        Log_oper.add_log("Normal>>开始载入跟踪模型")
        steel_model = YOLO()
        Log_oper.add_log("Normal>>完成载入跟踪模型成功")

        Log_oper.add_log("Normal>>开始载入多行识别模型")
        classes = {value['id']: value['name'] for value in json.load(open('char_model/char_class.json', 'r')).values()}
        colors = [np.random.randint(0, 256, 3).tolist() for _ in range(len(classes))]
        _, char_model = efficientdet(phi=2,weighted_bifpn=True,num_classes=len(classes),score_threshold=0.5)
        char_model.load_weights('char_model/char_model.h5', by_name=True)
        char_model_param={'image_size':768,'classes':classes,'score_threshold':0.5,'colors':colors}
        Log_oper.add_log("Normal>>完成载入多行识别模型")

        Log_oper.add_log("Normal>>开始载入单行识别模型")
        classes_mini = {value['id']: value['name'] for value in json.load(open('char_model_mini/char_class.json', 'r')).values()}
        colors_mini = [np.random.randint(0, 256, 3).tolist() for _ in range(len(classes_mini))]
        _, char_model_mini = efficientdet(phi=2,weighted_bifpn=True,num_classes=len(classes_mini),score_threshold=0.5)
        char_model_mini.load_weights('char_model_mini/char_model.h5', by_name=True)
        char_model_param_mini={'image_size':768,'classes':classes_mini,'score_threshold':0.5,'colors':colors_mini}
        Log_oper.add_log("Normal>>完成载入单行识别模型")
        
        Log_oper.add_log("Normal>>开始载入数字识别模型")
        classes_number = {value['id']: value['name'] for value in json.load(open('char_model_num/char_class.json', 'r')).values()}
        colors_number = [np.random.randint(0, 256, 3).tolist() for _ in range(len(classes_number))]
        _, char_model_number = efficientdet(phi=2,weighted_bifpn=True,num_classes=len(classes_number),score_threshold=0.5)
        char_model_number.load_weights('char_model_num/char_model.h5', by_name=True)
        char_model_param_number={'image_size':768,'classes':classes_number,'score_threshold':0.5,'colors':colors_number}
        Log_oper.add_log("Normal>>完成载入数字识别模型")
    
        Log_oper.add_log("Normal>>开始创建二级连接")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('191.168.162.192', 12001))
        t_send_heartbeat = threading.Thread(target=thread_send_heartbeat_to_l2,args=(s,Log_oper,))
        t_send_heartbeat.start()
        t_recv_info=HThreadRecvInfo((s,Log_oper,),"recv")       
        t_recv_info.start()   
        Log_oper.add_log("Normal>>完成成功连接到二级")
        
        steel_no_send={"SBM":False,"HTF1":False,"HTF2":False,"PRINT":False} # 当前钢板是否已经给二级发送至少一次钢板号，只要发送过就会被设置为True
        last_recv_res={"SBM":[1,1,1],"HTF1":[1,1,1],"HTF2":[1,1,1],"PRINT":[1,1,1]} #第1位：二级计划找到计数加1，范围1-3000 第2位：钢板是否在识别区 1为在0为不在 第3位：辊道转速情况 1为正转 0为停止 -1为倒转 
        time.sleep(5)#延时一会，让二级信息接收到后，再对变量进行更新，不让其使用默认值，另外感觉recv_res得到的是变量的地址，会跟着变
        recv_res=copy.deepcopy(t_recv_info.get_result()) 
        last_recv_res["SBM"]=copy.deepcopy(recv_res["SBM"])
        last_recv_res["HTF1"]=copy.deepcopy(recv_res["HTF1"])
        last_recv_res["HTF2"]=copy.deepcopy(recv_res["HTF2"])
        last_recv_res["PRINT"]=copy.deepcopy(recv_res["PRINT"])
        char_roi=None
        enable_l2_final_send={"SBM":False,"HTF1":False,"HTF2":False,"PRINT":False} #程序重启后钢板不在识别区时不发送数据
        last_recv_res_plan_counter={"SBM":copy.deepcopy(last_recv_res["SBM"][0]),"HTF1":copy.deepcopy(last_recv_res["HTF1"][0]),"HTF2":copy.deepcopy(last_recv_res["HTF2"][0]),"PRINT":copy.deepcopy(last_recv_res["PRINT"][0])} #通过2级发送的第一位计数判断是否还给二级发送，如果计数已变化则不再发送
        
        init_delete_imgfile(Log_oper,path_1,path_2,path_3,path_4)
        
        judge_num_sbm=0
        SCD_SBM_Oper=SteelCharDetect(1,Log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,char_model_number,char_model_param_number,s,10,path_1)
        judge_num_htf1=0
        SCD_HTF1_Oper=SteelCharDetect(2,Log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,char_model_number,char_model_param_number,s,10,path_2)
        judge_num_htf2=0
        SCD_HTF2_Oper=SteelCharDetect(3,Log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,char_model_number,char_model_param_number,s,10,path_3)
        judge_num_print=0
        SCD_PRINT_Oper=SteelCharDetect(4,Log_oper,steel_model,char_model,char_model_param,char_model_mini,char_model_param_mini,char_model_number,char_model_param_number,s,10,path_4)
        
        t_load_image_cam1 = threading.Thread(target=thread_load_camimg1, args=(Log_oper,path_1))
        t_load_image_cam1.start()
        t_load_image_cam2 = threading.Thread(target=thread_load_camimg2, args=(Log_oper,path_2))
        t_load_image_cam2.start()
        t_load_image_cam3 = threading.Thread(target=thread_load_camimg3, args=(Log_oper,path_3))
        t_load_image_cam3.start()
        t_load_image_cam4 = threading.Thread(target=thread_load_camimg4, args=(Log_oper,path_4))
        t_load_image_cam4.start()

    except Exception as err:
        Log_oper.add_log("Error>>初始化过程中出现错误{},程序自动重启".format(err))
        os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')
        
    #钢板状态更新
    def total_steel_state_update():
        global g_temp,g_temp_num
        recv_res=copy.deepcopy(t_recv_info.get_result()) 
        #抛丸机
        if recv_res["SBM"][1]==1:
            enable_l2_final_send["SBM"]=True
        if recv_res["SBM"][1]==0 and last_recv_res["SBM"][1]==1:        # 钢板退出时执行
            if recv_res["SBM"][2]>=0 and enable_l2_final_send["SBM"] is True:
                if steel_no_send["SBM"] is not True:
                    steel_no,steel_type,steel_size=SCD_SBM_Oper.get_send_char(char_roi,cache_limit=False)
                    if steel_no is not None:
                        SCD_SBM_Oper.send_char_to_l2(steel_no,steel_type,steel_size)
                    else:
                        if SCD_SBM_Oper.curr_char_img_info["char_roi"] is not None:
                            SCD_SBM_Oper.send_char_to_l2_not_steel_no()
                        else:
                            SCD_SBM_Oper.send_char_to_l2_not_img()
            SCD_SBM_Oper.cache_char=[]
        elif recv_res["SBM"][1]==1 and last_recv_res["SBM"][1]==0:      # 钢板重新进入后，上一次发送的板号置0
            steel_no_send["SBM"]=False
            last_recv_res_plan_counter["SBM"]=copy.deepcopy(recv_res["SBM"][0])
            SCD_SBM_Oper.last_steel_no="00000000000000"                         
            SCD_SBM_Oper.curr_char_img_info={"img_name":None,"char_roi":None,"src_img":None}
            SCD_SBM_Oper.curr_steel_img_info={"img_name":None,"char_roi":None,"src_img":None}
        last_recv_res["SBM"]=copy.deepcopy(recv_res["SBM"])
        #1号炉
        if recv_res["HTF1"][1]==1:
            enable_l2_final_send["HTF1"]=True
        if recv_res["HTF1"][1]==0 and last_recv_res["HTF1"][1]==1:      # 钢板退出时执行
            if recv_res["HTF1"][2]>=0 and enable_l2_final_send["HTF1"] is True:
                if steel_no_send["HTF1"] is not True:
                    steel_no,steel_type,steel_size=SCD_HTF1_Oper.get_send_char(char_roi,cache_limit=False)
                    if steel_no is not None:
                        SCD_HTF1_Oper.send_char_to_l2(steel_no,steel_type,steel_size)
                    else:
                        if SCD_HTF1_Oper.curr_char_img_info["char_roi"] is not None:
                            SCD_HTF1_Oper.send_char_to_l2_not_steel_no()
                        else:
                            SCD_HTF1_Oper.send_char_to_l2_not_img()
            SCD_HTF1_Oper.cache_char=[]
        elif recv_res["HTF1"][1]==1 and last_recv_res["HTF1"][1]==0:    # 钢板重新进入后，上一次发送的板号置0
            steel_no_send["HTF1"]=False
            last_recv_res_plan_counter["HTF1"]=copy.deepcopy(recv_res["HTF1"][0])
            SCD_HTF1_Oper.last_steel_no="00000000000000"               # 针对炉前来回倒板的情况，为避免重复识别发送
            SCD_HTF1_Oper.curr_char_img_info={"img_name":None,"char_roi":None,"src_img":None}
            SCD_HTF1_Oper.curr_steel_img_info={"img_name":None,"char_roi":None,"src_img":None}
            g_temp=True
            g_temp_num=0
        #还未在二级计划中找到号并且截取到了字符图像
        if steel_no_send["HTF1"] is not True and SCD_HTF1_Oper.curr_char_img_info["char_roi"] is not None:
            if g_temp is True and g_temp_num>60:
                SCD_HTF1_Oper.send_char_to_l2_not_steel_no()
                g_temp=False
        g_temp_num=g_temp_num+1
        #
        last_recv_res["HTF1"]=copy.deepcopy(recv_res["HTF1"])
        #2号炉
        if recv_res["HTF2"][1]==1:
            enable_l2_final_send["HTF2"]=True
        if recv_res["HTF2"][1]==0 and last_recv_res["HTF2"][1]==1:      # 钢板退出时执行
            if recv_res["HTF2"][2]>=0 and enable_l2_final_send["HTF2"] is True:
                if steel_no_send["HTF2"] is not True:
                    steel_no,steel_type,steel_size=SCD_HTF2_Oper.get_send_char(char_roi,cache_limit=False)
                    if steel_no is not None:
                        SCD_HTF2_Oper.send_char_to_l2(steel_no,steel_type,steel_size)
                    else:
                        if SCD_HTF2_Oper.curr_char_img_info["char_roi"] is not None:
                            SCD_HTF2_Oper.send_char_to_l2_not_steel_no()
                        else:
                            SCD_HTF2_Oper.send_char_to_l2_not_img()
            SCD_HTF2_Oper.cache_char=[]
        elif recv_res["HTF2"][1]==1 and last_recv_res["HTF2"][1]==0:    # 钢板重新进入后，上一次发送的板号置0
            steel_no_send["HTF2"]=False
            last_recv_res_plan_counter["HTF2"]=copy.deepcopy(recv_res["HTF2"][0])
            #SCD_HTF2_Oper.last_steel_no="00000000000000"               # 针对炉前来回倒板的情况，为避免重复识别发送                       
            SCD_HTF2_Oper.curr_char_img_info={"img_name":None,"char_roi":None,"src_img":None}
            SCD_HTF2_Oper.curr_steel_img_info={"img_name":None,"char_roi":None,"src_img":None}
        last_recv_res["HTF2"]=copy.deepcopy(recv_res["HTF2"])
        #标印
        if recv_res["PRINT"][1]==1:
            enable_l2_final_send["PRINT"]=True
        if recv_res["PRINT"][1]==0 and last_recv_res["PRINT"][1]==1:    # 钢板退出时执行
            if recv_res["PRINT"][2]>=0 and enable_l2_final_send["PRINT"] is True:
                if steel_no_send["PRINT"] is not True:
                    steel_no,steel_type,steel_size=SCD_PRINT_Oper.get_send_char(char_roi,cache_limit=False)
                    if steel_no is not None:
                        SCD_PRINT_Oper.send_char_to_l2(steel_no,steel_type,steel_size)
                    else:
                        if SCD_PRINT_Oper.curr_char_img_info["char_roi"] is not None:
                            SCD_PRINT_Oper.send_char_to_l2_not_steel_no()
                        else:
                            SCD_PRINT_Oper.send_char_to_l2_not_img()
            SCD_PRINT_Oper.cache_char=[]
        elif recv_res["PRINT"][1]==1 and last_recv_res["PRINT"][1]==0:  # 钢板重新进入后，上一次发送的板号置0
            steel_no_send["PRINT"]=False
            last_recv_res_plan_counter["PRINT"]=copy.deepcopy(recv_res["PRINT"][0])
            SCD_PRINT_Oper.last_steel_no="00000000000000"                         
            SCD_PRINT_Oper.curr_char_img_info={"img_name":None,"char_roi":None,"src_img":None}
            SCD_PRINT_Oper.curr_steel_img_info={"img_name":None,"char_roi":None,"src_img":None}
        last_recv_res["PRINT"]=copy.deepcopy(recv_res["PRINT"])
    
    # 主循环
    while True:
        try:
            total_steel_state_update()
            recv_res=copy.deepcopy(t_recv_info.get_result())
            
            if not image_cache_cam1.empty():
                Log_oper.add_log("Normal>>-----------------抛丸机前字符识别-----------------当前剩余待处理图像数量为{}张".format(image_cache_cam1.qsize()))
                img_info = image_cache_cam1.get()
                img_path=img_info["img_path"]
                img_name=img_info["img_name"]
                img_data=img_info['img_data']
                if recv_res["SBM"][0]==last_recv_res_plan_counter["SBM"]:    #二级还未收到计划中可找到的号，需要进行识别
                    char_label,char_roi,top_offset,bottom_offset=SCD_SBM_Oper.detect_steel(img_path,img_name,img_data)
                    if char_roi is not None:
                        if char_label != 'tchar':
                            SCD_SBM_Oper.detect_char(char_roi,img_data,img_name,top_offset,bottom_offset)
                        else:
                            SCD_SBM_Oper.detect_char_mini(char_roi,img_data,img_name,top_offset,bottom_offset)
                    steel_no,steel_type,steel_size=SCD_SBM_Oper.get_send_char(char_roi,cache_limit=True)
                    if steel_no is not None:
                        recv_res=copy.deepcopy(t_recv_info.get_result())
                        if recv_res["SBM"][2]>=0:  #辊道速度不为负，才进行钢板号发送
                            SCD_SBM_Oper.send_char_to_l2(steel_no,steel_type,steel_size)
                            steel_no_send["SBM"]=True

                total_steel_state_update()

            
            if not image_cache_cam2.empty():
                Log_oper.add_log("Normal>>-----------------一号加热炉前字符识别-----------------当前剩余待处理图像数量为{}张".format(image_cache_cam2.qsize()))
                img_info = image_cache_cam2.get()
                img_path=img_info["img_path"]
                img_name=img_info["img_name"]
                img_data=img_info['img_data']
                
                if recv_res["HTF1"][0]==last_recv_res_plan_counter["HTF1"]:    #二级还未收到计划中可找到的号，需要进行识别
                    char_label,char_roi,top_offset,bottom_offset=SCD_HTF1_Oper.detect_steel(img_path,img_name,img_data)
                    if char_roi is not None:
                        if char_label != 'tchar':
                            SCD_HTF1_Oper.detect_char(char_roi,img_data,img_name,top_offset,bottom_offset)
                        else:
                            SCD_HTF1_Oper.detect_char_mini(char_roi,img_data,img_name,top_offset,bottom_offset)
                    steel_no,steel_type,steel_size=SCD_HTF1_Oper.get_send_char(char_roi,cache_limit=True)
                    if steel_no is not None:
                        recv_res=copy.deepcopy(t_recv_info.get_result())
                        if recv_res["HTF1"][2]>=0:  #辊道速度不为负，才进行钢板号发送
                            SCD_HTF1_Oper.send_char_to_l2(steel_no,steel_type,steel_size)
                            steel_no_send["HTF1"]=True
                                  
                total_steel_state_update()     # 一级状态获取检查是否有需要发送钢板号

            
            if not image_cache_cam3.empty():
                Log_oper.add_log("Normal>>-----------------二号加热炉前字符识别-----------------当前剩余待处理图像数量为{}张".format(image_cache_cam3.qsize()))
                img_info = image_cache_cam3.get()
                img_path=img_info["img_path"]
                img_name=img_info["img_name"]
                img_data=img_info['img_data']
                 
                if recv_res["HTF2"][0]==last_recv_res_plan_counter["HTF2"]:    #二级还未收到计划中可找到的号，需要进行识别
                    char_label,char_roi,top_offset,bottom_offset=SCD_HTF2_Oper.detect_steel(img_path,img_name,img_data)
                    if char_roi is not None:
                        if char_label != 'tchar':
                            SCD_HTF2_Oper.detect_char(char_roi,img_data,img_name,top_offset,bottom_offset)
                        else:
                            SCD_HTF2_Oper.detect_char_mini(char_roi,img_data,img_name,top_offset,bottom_offset)
                    steel_no,steel_type,steel_size=SCD_HTF2_Oper.get_send_char(char_roi,cache_limit=True)
                    if steel_no is not None:
                        recv_res=copy.deepcopy(t_recv_info.get_result())
                        if recv_res["HTF2"][2]>=0:  #辊道速度不为负，才进行钢板号发送
                            SCD_HTF2_Oper.send_char_to_l2(steel_no,steel_type,steel_size)
                            steel_no_send["HTF2"]=True

                total_steel_state_update()     # 一级状态获取检查是否有需要发送钢板号

            
            if not image_cache_cam4.empty():
                Log_oper.add_log("Normal>>-----------------喷印前字符识别-----------------当前剩余待处理图像数量为{}张".format(image_cache_cam4.qsize()))
                img_info = image_cache_cam4.get()
                img_path=img_info["img_path"]
                img_name=img_info["img_name"]
                img_data=img_info['img_data']
                 
                if recv_res["PRINT"][0]==last_recv_res_plan_counter["PRINT"]:    #二级还未收到计划中可找到的号，需要进行识别
                    char_label,char_roi,top_offset,bottom_offset=SCD_PRINT_Oper.detect_steel(img_path,img_name,img_data)
                    if char_roi is not None:
                        if char_label != 'tchar':
                            SCD_PRINT_Oper.detect_char(char_roi,img_data,img_name,top_offset,bottom_offset)
                        else:
                            SCD_PRINT_Oper.detect_char_mini(char_roi,img_data,img_name,top_offset,bottom_offset)
                    steel_no,steel_type,steel_size=SCD_PRINT_Oper.get_send_char(char_roi,cache_limit=True)
                    if steel_no is not None:
                        recv_res=copy.deepcopy(t_recv_info.get_result())
                        if recv_res["PRINT"][2]>=0:  #辊道速度不为负，才进行钢板号发送
                            SCD_PRINT_Oper.send_char_to_l2(steel_no,steel_type,steel_size)
                            steel_no_send["PRINT"]=True

                total_steel_state_update()     # 一级状态获取检查是否有需要发送钢板号

        except Exception as err:
            Log_oper.add_log("Error>>主循环执行中出现错误{},程序自动重启".format(err))
            os.system('taskkill /IM ArNTSteelDefectsClassifier64.exe /F')        
    steel_model.close_session()
