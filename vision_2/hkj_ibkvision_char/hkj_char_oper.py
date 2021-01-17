import os
import time
import json
import math
import copy
from operator import itemgetter

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
    
def cal_iou(box1, box2):
    ymin1, xmin1, ymax1, xmax1 = box1
    ymin2, xmin2, ymax2, xmax2 = box2
    # 计算每个矩形的面积
    s1 = (xmax1 - xmin1) * (ymax1 - ymin1)  # C的面积
    s2 = (xmax2 - xmin2) * (ymax2 - ymin2)  # G的面积
    # 计算相交矩形
    xmin = max(xmin1, xmin2)
    ymin = max(ymin1, ymin2)
    xmax = min(xmax1, xmax2)
    ymax = min(ymax1, ymax2)
    w = max(0, xmax - xmin)
    h = max(0, ymax - ymin)
    area = w * h  # C∩G的面积
    iou = area / (s1 + s2 - area)
    return iou

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
    #针对没有识别到南钢标记的
    if base_box is None:
        base_box=[9999, 9999, 9999, 9999,'*',0]
        for i in range(0,len(char_boxs)):
            if char_boxs[i][4]!='#' and char_boxs[i][4]!='*':
                b=math.sqrt(int(base_box[0])*int(base_box[0])+int(base_box[1])*int(base_box[1]))
                c=math.sqrt(int(char_boxs[i][0])*int(char_boxs[i][0])+int(char_boxs[i][1])*int(char_boxs[i][1]))
                if b>c:
                    base_box=copy.deepcopy(char_boxs[i])
        base_box[0]=base_box[0]-1
        base_box[2]=base_box[2]-1
    #
    if char_width_n>0 and char_height_n>0:
        char_width_mean=char_width_mean/char_width_n
        char_height_mean=char_height_mean/char_height_n
        if base_box is not None:
            base_x=(base_box[2]+base_box[0])/2
            base_y=(base_box[3]+base_box[1])/2
            #数据进行一次x方向排序
            char_boxs.sort(key=itemgetter(0), reverse=False) 
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
                        base_y=center_y
                    else:
                        offset_row_boxs.append(char_boxs[i])
                        if center_y<offset_row_boxs_min_y:
                            offset_row_boxs_min_y=center_y
            one_row_boxs.sort(key=itemgetter(0), reverse=False)     
            steel_no=''
            steel_no_score=0
            char_interval=[]
            if len(one_row_boxs)>0:
                b_x=(one_row_boxs[0][2]+one_row_boxs[0][0])/2
                b_y=(one_row_boxs[0][3]+one_row_boxs[0][1])/2
            is_num=False
            last_index=-1
            for i in range(0,len(one_row_boxs)):
                n_x=(one_row_boxs[i][2]+one_row_boxs[i][0])/2
                n_y=(one_row_boxs[i][3]+one_row_boxs[i][1])/2
                if is_number(str(one_row_boxs[i][4])) is True:
                    if int(one_row_boxs[i][4])>0 and int(one_row_boxs[i][4])<=2: #针对第一位的年份做强制限制
                        is_num=True
                if is_num is True and abs(n_y-b_y)<char_height_mean:
                    b_x,b_y=n_x,n_y
                    steel_no=steel_no+str(one_row_boxs[i][4])
                    steel_no_score=steel_no_score+one_row_boxs[i][5]
                    if last_index != -1:
                        char_interval.append(max(0,one_row_boxs[i][0]-one_row_boxs[last_index][2]))
                    last_index=i
                if len(steel_no)==14:
                    if max(char_interval)>char_width_mean:
                        steel_no=list(steel_no)
                        steel_no[0]="@"
                        steel_no="".join(steel_no)
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
            return steel_no,steel_no_score,steel_type,steel_size
    return '',0,'',''


def get_steel_info_mini(boxes, scores, labels, classes):
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

        char_width_mean=char_width_mean+(xmax-xmin)
        char_height_mean=char_height_mean+(ymax-ymin)
        char_width_n=char_width_n+1
        char_height_n=char_height_n+1
        char_boxs.append(temp_box)
    if char_width_n>0 and char_height_n>0:
        char_width_mean=char_width_mean/char_width_n
        char_height_mean=char_height_mean/char_height_n
        
        char_boxs.sort(key=itemgetter(0), reverse=False)
        if len(char_boxs)>0:
            base_box=char_boxs[0]
            base_x=(base_box[2]+base_box[0])/2 - 1
            base_y=(base_box[3]+base_box[1])/2 - 1
        steel_no=''
        steel_no_score=0
        for i in range(0,len(char_boxs)):
            center_x=(char_boxs[i][2]+char_boxs[i][0])/2
            center_y=(char_boxs[i][3]+char_boxs[i][1])/2
            if center_x>base_x:
                if abs(center_y-base_y)<char_height_mean:
                    steel_no=steel_no+str(char_boxs[i][4])
                    steel_no_score=steel_no_score+char_boxs[i][5]
                    base_y=center_y
            if len(steel_no)==14:
                break
            
        #返回数据
        steel_no_score=steel_no_score/14
        #if char_interval<char_width_mean:
        return steel_no,steel_no_score
    return '',0
