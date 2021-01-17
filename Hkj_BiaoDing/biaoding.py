import cv2
import numpy as np
import glob
 
# 设置寻找亚像素角点的参数，采用的停止准则是最大循环次数30和最大误差容限0.001
criteria = (cv2.TERM_CRITERIA_MAX_ITER | cv2.TERM_CRITERIA_EPS, 30, 0.001)
 
# 获取标定板角点的位置
# 标定时要注意的坑，就是标定板一定要尽量充满图像，不然标定完会报错
#row,col=11,8 #2560
row,col=9,6 #1920
objp = np.zeros((row*col,3), np.float32)
objp[:,:2] = np.mgrid[0:row,0:col].T.reshape(-1,2)  # 将世界坐标系建在标定板上，所有点的Z坐标全部为0，所以只需要赋值x和y
 
obj_points = []    # 存储3D点
img_points = []    # 存储2D点
 
images = glob.glob("mask_1920/*.bmp")
for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    size = gray.shape[::-1]
    ret, corners = cv2.findChessboardCorners(gray, (row,col), None)
 
    if ret:
        obj_points.append(objp)
 
        print(corners[0])
        corners2 = cv2.cornerSubPix(gray, corners, (3,3), (-1,-1), criteria)  # 在原角点的基础上寻找亚像素角点
        print(corners2[0])
        if corners2.any():
            img_points.append(corners2)
            print(len(corners2))
        else:
            img_points.append(corners)
            print(len(corners))
 
        cv2.drawChessboardCorners(img, (row,col), corners, ret)   # 记住，OpenCV的绘制函数一般无返回值
        cv2.namedWindow('img',0)
        cv2.imshow('img', img)
        cv2.waitKey(100)
 
print(len(img_points),img.shape)
cv2.destroyAllWindows()
 
# 标定
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points,size, None, None)
 
print("ret:",ret)
print("mtx:\n",mtx)        # 内参数矩阵
print("dist:\n",dist)      # 畸变系数   distortion cofficients = (k_1,k_2,p_1,p_2,k_3)
print("rvecs:\n",rvecs)    # 旋转向量  # 外参数
print("tvecs:\n",tvecs)    # 平移向量  # 外参数
 
print("-----------------------------------------------------")
# 畸变校正
img = cv2.imread(images[0])
h, w = img.shape[:2]
newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))
print(img.shape)

print("------------------使用undistort函数-------------------")
dst = cv2.undistort(img,mtx,dist,None,newcameramtx)
x,y,w,h = roi
print(roi)
dstc = dst[y:y+h,x:x+w]
cv2.imwrite('calibresultu.jpg', dstc)
print("方法一:dst的大小为:", dstc.shape)
 
print("-------------------使用重映射的方式-----------------------")
mapx,mapy = cv2.initUndistortRectifyMap(mtx,dist,None,newcameramtx,(w,h),5)  # 获取映射方程
dst = cv2.remap(img,mapx,mapy,cv2.INTER_LINEAR)      # 重映射
x,y,w,h = roi
dstd = dst[y:y+h,x:x+w]
cv2.imwrite('calibresultm.jpg', dstd)
print("方法二:dst的大小为:", dstd.shape)        # 图像比方法一的小

print("-------------------计算反向投影误差-----------------------")
tot_error = 0
for i in range(0,len(obj_points)):
    img_points2, _ = cv2.projectPoints(obj_points[i],rvecs[i],tvecs[i],mtx,dist)
    error = cv2.norm(img_points[i],img_points2, cv2.NORM_L2)/len(img_points2)
    tot_error += error
 
mean_error = tot_error/len(obj_points)
print("total error: ", tot_error)
print("mean error: ", mean_error)