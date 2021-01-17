import os
import cv2
import configparser
import numpy as np
from xml.etree import ElementTree as ET
from keras.models import load_model
from PIL import Image
class Xml:

    def __init__(self, file_name):
        self.file_name = file_name
        self.per = ET.parse(self.file_name)

    def read_info(self, key_info):  # key: ef:'./缺陷类别/类别1',只能接收1层
        p = self.per.findall(key_info)
        for one_per in p:
            if len(one_per) == 0:
                return one_per.text
            else:
                key_value = {}
                for child in one_per.getchildren():
                    key_value[child.tag] = child.text
                return key_value
        return None


class Ini:

    def __init__(self, file_name):
        self.file_name = file_name
        self.conf = configparser.ConfigParser()

    def read_info(self, section_info, key_info):
        self.conf.read(self.file_name)
        value_info = self.conf.get(section_info, key_info)
        return value_info

    def write_section(self, section_info):
        self.conf.add_section(section_info)
        self.conf.write(open(self.file_name, 'w'))

    def write_key_value(self, section_info, key_info, value_info):
        self.conf.set(section_info, key_info, str(value_info))
        self.conf.write(open(self.file_name, 'w'))
        
class Classifier:

    def __init__(self, img_width, img_height, model_name):

        self.img_width = img_width
        self.img_height = img_height
        self.model_name = model_name
        self.model = None

    def load_model(self):
        if os.path.exists(self.model_name):
            self.model = load_model(self.model_name)
            return self.model
        else:
            return None

    def get_img(self, img_path):
        pass

    def predict_img(self, image):
        pass

    def get_norm_img(self, img_list):
        img_arr = []
        for i in range(0, len(img_list)):
            img = img_list[i]
            #img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            img = cv2.resize(img, (self.img_width, self.img_height))
            img = np.asarray(img, np.float32)
            img = img / 255.0
            img_arr.append(img)
        if len(img_arr) > 0:
            img_arr = np.stack(img_arr, axis=0).astype(np.float32)
            img_arr = img_arr.reshape(img_arr.shape[0], self.img_height, self.img_width, 3)
            return img_arr
        else:
            return None

    def get_img_arr(self, img_paths):
        img_arr = []
        effect_paths = []
        for image_path in img_paths:
            if os.path.exists(image_path):
                mark = -1
                try:
                    im = Image.open(image_path)
                    im = im.convert("RGB")
                    im = im.resize((self.img_width, self.img_height))
                    im = np.asarray(im, np.float32)
                    im = im / 255.0
                    mark = 1
                except:
                    mark = 0
                if mark == 1:
                    img_arr.append(im)
                    effect_paths.append(image_path)
        if len(img_arr) > 0:
            img_arr = np.stack(img_arr, axis=0).astype(np.float32)
            img_arr = img_arr.reshape(img_arr.shape[0], self.img_height, self.img_width, 3)
            return effect_paths, img_arr
        else:
            return None, None

    def predict_img_arr(self, image_arr):
        preds_result = []
        preds_confidence = []
        class_scores = self.model.predict(image_arr, batch_size=image_arr.shape[0])
        for class_score in class_scores:
            pre_class = 0
            max_score = 0.0
            for n in range(len(class_score)):
                if class_score[n] > max_score:
                    max_score = class_score[n]
                    pre_class = n
            preds_result.append(pre_class)
            preds_confidence.append(max_score)
        return preds_result, preds_confidence

def get_convert_from_class_table(file_path, log_oper, mode=0):
    if os.path.exists(file_path):
        xml_oper = Xml(file_path)
        class_num = xml_oper.read_info('./缺陷类别/类别总数')

        class_convert_table = {}
        for i in range(int(class_num)):
            key_info = './缺陷类别/类别%d' % i
            values = xml_oper.read_info(key_info)
            internal_no = ""
            internal_name = ""
            external_no = ""
            for key in values:
                if key == "内部编号":
                    internal_no = values[key]
                elif key == "名称":
                    internal_name = values[key]
                elif key == "外部编号":
                    external_no = values[key]
            if mode == 0:
                class_convert_table[internal_no] = external_no
            elif mode == 1:
                class_convert_table[internal_no] = internal_name
            elif mode == 2:
                class_convert_table[internal_name] = internal_no
        return class_convert_table
    else:
        log_oper.add_log("@@Error：未检测到{}文件，请检查！！！".format(file_path))
        return None


def get_convert_from_ini_config_file(file_path, log_oper, mode=0):
    if os.path.exists(file_path):
        ini_oper = Ini(file_path)
        class_convert_table = {}
        class_num = ini_oper.read_info("Classifier", "ClassNum")
        img_size = ini_oper.read_info("Classifier", "ImgSize")
        model = ini_oper.read_info("Classifier", "Model")
        for i in range(int(class_num)):
            class_no = "Class%d" % i
            internal_no = ini_oper.read_info("ClassConversion", class_no)
            class_convert_table[i] = internal_no
        return class_convert_table, img_size, class_num, model
    else:
        log_oper.add_log("@@Error：未检测到{}文件，请检查！！！".format(file_path))
        return None, None, None, None
