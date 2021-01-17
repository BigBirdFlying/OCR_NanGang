// Hkj_Character_RecognitionDlg.h : ͷ�ļ�
//

#pragma once
#include "afxcmn.h"
#include "H_General_Def.h"
#include "HFile.h"
#include "HThread.h"
#include "afxwin.h"
#include "H_DataDef.h"
//#include "HCNetSDK.h"
//#include "PlayM4.h"
#define _CAMERA_NUM_  8

typedef struct tagThreadInfo
{
	int iSecond;     
}ThreadInfo,*PThreadInfo;  

// CHkj_Character_RecognitionDlg �Ի���
class CHkj_Character_RecognitionDlg : public CDialog
{
// ����
public:
	CHkj_Character_RecognitionDlg(CWnd* pParent = NULL);	// ��׼���캯��

// �Ի�������
	enum { IDD = IDD_HKJ_CHARACTER_RECOGNITION_DIALOG };

	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV ֧��


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
	static HWND			m_hPlayWnd;
	HThread				m_hThread[_CAMERA_NUM_];
	static long			m_iImageSaveIndex[_CAMERA_NUM_];
	static CString		m_iImageSavePath[_CAMERA_NUM_];
	static int			m_iImgWidth[_CAMERA_NUM_];
	static int			m_iImgHeight[_CAMERA_NUM_];
	ThreadInfo			m_ThreadInfo;
	
	static ConfigCameraSet		m_ConfigCameraSet;

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
	static void GetCameraMatrix_2560(int iImgWidth,int iImgHeight,cv::Mat &cameraMatrix,cv::Mat &distCoeffs,cv::Mat &newMatrix,cv::Rect &rectRoi);
	static void GetCameraMatrix_1920(int iImgWidth,int iImgHeight,cv::Mat &cameraMatrix,cv::Mat &distCoeffs,cv::Mat &newMatrix,cv::Rect &rectRoi);
	static void RectifyImage(const cv::Mat src ,cv::Mat& dst,cv::Mat cameraMatrix,cv::Mat distCoeffs,cv::Mat newMatrix,cv::Rect rectRoi); 
	static void RotataImage(const cv::Mat src ,cv::Mat& dst,int iAngle);
	static void SaveImageOpenCV(cv::Mat src ,CString strImgPath, long iIndex);

	static void CALLBACK fRealDataCallBack(LONG lRealHandle,DWORD dwDataType,BYTE *pBuffer,DWORD dwBufSize,void *pUser);
	static void CALLBACK DecCBFun(long nPort,char * pBuf,long nSize,FRAME_INFO * pFrameInfo, long nReserved1,long nReserved2);
// ʵ��
protected:
	HICON m_hIcon;

	// ���ɵ���Ϣӳ�亯��
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
