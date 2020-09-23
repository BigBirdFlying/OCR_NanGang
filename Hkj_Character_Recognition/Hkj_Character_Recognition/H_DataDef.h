#pragma once

typedef struct tagConfigCamera
{
	int iCamNo;
	CString strIP;
	int iPort;
	CString strUserName;
	CString strPassword;
	int iImgWidth;
	int iImgHeight;
	bool bIsAutoSave;
	int iRotateAngle;
	float fJudgeLeftRatio;
	float fJudgeRightRatio;
	float fJudgeSaveImgLimit;
	CString strImgPath;
	long iCamID;
	//LOCAL_DEVICE_INFO tagDeviceInfo;
}ConfigCamera,*PConfigCamera;
typedef struct tagConfigCameraSet
{
	enum{MAX_ITEMNUM=16};
	ConfigCamera Items[MAX_ITEMNUM];
	int iItemNum;
}ConfigCameraSet,*PConfigCameraSet;

