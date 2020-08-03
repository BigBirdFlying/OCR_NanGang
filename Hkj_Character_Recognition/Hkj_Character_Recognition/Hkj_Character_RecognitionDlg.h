// Hkj_Character_RecognitionDlg.h : 头文件
//

#pragma once
#include "afxcmn.h"
#include "H_General_Def.h"
#include "HFile.h"
#include "HThread.h"
#include "afxwin.h"
//#include "HCNetSDK.h"
//#include "PlayM4.h"

typedef struct tagConfigCamera
{
	int iCamNo;
	CString strIP;
	int iPort;
	CString strUserName;
	CString strPassword;
	bool bIsAutoSave;
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

typedef struct tagThreadInfo
{
	int iSecond;     
}ThreadInfo,*PThreadInfo;  

// CHkj_Character_RecognitionDlg 对话框
class CHkj_Character_RecognitionDlg : public CDialog
{
// 构造
public:
	CHkj_Character_RecognitionDlg(CWnd* pParent = NULL);	// 标准构造函数

// 对话框数据
	enum { IDD = IDD_HKJ_CHARACTER_RECOGNITION_DIALOG };

	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV 支持


public:
	HTREEITEM			m_hDevItem;
	bool				m_bIsPlaying;
	long				m_lPlayHandle;
	long				m_lShowPlayHandle;
	int					m_iCurChanIndex;
	int					m_iCameraNum;

	static long			m_nPort;
	static long			m_iSaveIndex;
	static int			m_iSaveInterval;
	static int			m_iImgWidth;
	static int			m_iImgHeight;
	static HWND			m_hPlayWnd;
	HThread				m_hThread[8];
	static long			m_iImageSaveIndex[8];
	static CString		m_iImageSavePath[8];
	ThreadInfo			m_ThreadInfo;
	static cv::Mat		m_cameraMatrix;
	static cv::Mat		m_distCoeffs;
	static cv::Mat		m_newMatrix;
	static cv::Rect		m_rectRoi;

	ConfigCameraSet		m_ConfigCameraSet;
	HFile_log			m_LogOper;
	LOCAL_DEVICE_INFO	m_tagDeviceInfo;
	
	char* WideCharToMultiChar(CString str);
	bool LoadConfigFile(CString strPath);
	long ConnectCamera(CString strIP,int iPort,CString strUser,CString strPWD);
	void CreateDeviceTree();
	void PlayCameraChannel(int Index);
	void StartPlay(int iIndex);
	void StopPlay();
	void EnterCallback(int iIndex);
	void SaveImage(CString strImgPath,int iIndex);
	bool GetCameraImage(LONG& lUserID);

	static CString GetAppPath();
	static bool GetCameraImageLoop(LONG lCamNO,LONG lUserID);
	static UINT ThreadProc(LPVOID pParam);
	static void GetCameraMatrix();
	static void RectifyImage(cv::Mat src ,cv::Mat& dst); 
	static void SaveImageOpenCV(cv::Mat src ,CString strImgPath, long iIndex);

	static void CALLBACK fRealDataCallBack(LONG lRealHandle,DWORD dwDataType,BYTE *pBuffer,DWORD dwBufSize,void *pUser);
	static void CALLBACK DecCBFun(long nPort,char * pBuf,long nSize,FRAME_INFO * pFrameInfo, long nReserved1,long nReserved2);
// 实现
protected:
	HICON m_hIcon;

	// 生成的消息映射函数
	virtual BOOL OnInitDialog();
	afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	DECLARE_MESSAGE_MAP()
public:
	CTreeCtrl m_treeCtrl_Camera;
	afx_msg void OnNMDblclkTreeCamera(NMHDR *pNMHDR, LRESULT *pResult);
	CComboBox m_comboPicType;
	afx_msg void OnBnClickedButtonCapture();
	afx_msg void OnClose();
};
