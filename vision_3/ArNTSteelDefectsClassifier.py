from hkj_ibkvision_char.hkj_steel_char_detect import steel_char_detect
   

def Main():
    path_1={"path_camera":r"D:\ArNTCameraImage\Camera_No1\CameraImg_src",
            "path_ref":r"D:\ArNTCameraImage\Camera_No1\CameraImg_ref",
            "path_steel":r"D:\ArNTCameraImage\Camera_No1\CameraImg_steel",
            'path_char':r"D:\ArNTCameraImage\Camera_No1\CameraImg_char",
            "path_char_l2":r"D:\PlatePhoto\SBM"}
    path_2={"path_camera":r"D:\ArNTCameraImage\Camera_No2\CameraImg_src",
            "path_ref":r"D:\ArNTCameraImage\Camera_No2\CameraImg_ref",
            "path_steel":r"D:\ArNTCameraImage\Camera_No2\CameraImg_steel",
            'path_char':r"D:\ArNTCameraImage\Camera_No2\CameraImg_char",
            "path_char_l2":r"D:\PlatePhoto\HTF1"}
    path_3={"path_camera":r"D:\ArNTCameraImage\Camera_No3\CameraImg_src",
            "path_ref":r"D:\ArNTCameraImage\Camera_No3\CameraImg_ref",
            "path_steel":r"D:\ArNTCameraImage\Camera_No3\CameraImg_steel",
            'path_char':r"D:\ArNTCameraImage\Camera_No3\CameraImg_char",
            "path_char_l2":r"D:\PlatePhoto\HTF2"}
    path_4={"path_camera":r"D:\ArNTCameraImage\Camera_No4\CameraImg_src",
            "path_ref":r"D:\ArNTCameraImage\Camera_No4\CameraImg_ref",
            "path_steel":r"D:\ArNTCameraImage\Camera_No4\CameraImg_steel",
            'path_char':r"D:\ArNTCameraImage\Camera_No4\CameraImg_char",
            "path_char_l2":r"D:\PlatePhoto\PRINT"}
    steel_char_detect(path_1,path_2,path_3,path_4)


if __name__ == "__main__":
    Main()
