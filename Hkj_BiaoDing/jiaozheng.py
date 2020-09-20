import cv2
import numpy as np
 
def undistort(frame):
    fx = 1996.731
    cx = 1301.808
    fy = 1997.605
    cy = 669.558
    k1, k2, p1, p2, k3 = -0.394368, 0.142365, 0.000733, 0.001086, -0.014611
    
    '''
    fx = 2007.023
    cx = 1319.129
    fy = 2019.655
    cy = 633.281
    k1, k2, p1, p2, k3 = -0.5138, 1.0984, -0.0001534, -0.0008397, -2.514369
    '''
    
    # 相机坐标系到像素坐标系的转换矩阵
    k = np.array([
        [fx, 0, cx],
        [0, fy, cy],
        [0, 0, 1]
    ])
    # 畸变系数
    d = np.array([
        k1, k2, p1, p2, k3
    ])
    hh, ww = frame.shape[:2]
    #mapx, mapy = cv2.initUndistortRectifyMap(k, d, None, k, (w, h), 5)
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(k,d,(ww,hh),1,(ww,hh))
    dst = cv2.undistort(frame,k,d,None,newcameramtx)
    x,y,w,h = roi
    dst = dst[y:y+h,x:x+w]
    #dst = cv2.resize(dst,(w,int(w*(hh/ww))))
    #mapx,mapy = cv2.initUndistortRectifyMap(k,d,None,newcameramtx,(w,h),5)  # 获取映射方程
    #dst = cv2.remap(frame,mapx,mapy,cv2.INTER_CUBIC) 
    return dst
 
def rotate_bound(image, angle):
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    # perform the actual rotation and return the image
    return cv2.warpAffine(image, M, (nW, nH))

import glob   
images = glob.glob(r"daotu/*.jpg")
for fname in images:
    img=cv2.imread(fname,0)
    rotate=rotate_bound(img,180)
    cv2.imwrite(fname,rotate)
cv2.waitKey(0)
'''   
img=cv2.imread("img.jpg",0)
rotate=rotate_bound(img,180)
cv2.namedWindow("rotate",0)
cv2.imshow("rotate",rotate)
cv2.imwrite("rr.jpg",rotate)
cv2.waitKey(0)'''

img=cv2.imread("test.jpg",0)
print(img.shape)
cv2.namedWindow("src",0)
cv2.imshow("src",img)


dst=undistort(img)
print(dst.shape)
cv2.imwrite("test_res.bmp",dst)
cv2.namedWindow("dst",0)
cv2.imshow("dst",dst)

pts1 = np.float32([[258, 188], [366, 160], [330, 426]]) #11664+784=12448 112
pts2 = np.float32([[258, 188], [370, 188], [258, 436]]) #5184+56644=61828 248
M = cv2.getAffineTransform(pts1,pts2)
res = cv2.warpAffine(dst,M,(dst.shape[1],dst.shape[0]*2))
print(res.shape)
cv2.imwrite("test_res_map.bmp",res)
cv2.namedWindow("res",0)
cv2.imshow("res",res)
cv2.waitKey(0)