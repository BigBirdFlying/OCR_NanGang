import os
import time
import json
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
            if len(one_row_boxs)>0:
                b_x=(one_row_boxs[0][2]+one_row_boxs[0][0])/2
                b_y=(one_row_boxs[0][3]+one_row_boxs[0][1])/2
            is_num=False
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
        steel_no=''
        steel_no_score=0
        for i in range(0,len(char_boxs)):
            steel_no=steel_no+str(one_row_boxs[i][4])
            steel_no_score=steel_no_score+one_row_boxs[i][5]

            if len(steel_no)==14:
                break
            
            #返回数据
            steel_no_score=steel_no_score/14
            #if char_interval<char_width_mean:
            return steel_no,steel_no_score
    return '',0