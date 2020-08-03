// Hkj_Character_RecognitionDlg.cpp : ʵ���ļ�
//

#include "stdafx.h"
#include "Hkj_Character_Recognition.h"
#include "Hkj_Character_RecognitionDlg.h"
#include "HFile.h"


#ifdef _DEBUG
#define new DEBUG_NEW
#endif


// ����Ӧ�ó��򡰹��ڡ��˵���� CAboutDlg �Ի���

class CAboutDlg : public CDialog
{
public:
	CAboutDlg();

// �Ի�������
	enum { IDD = IDD_ABOUTBOX };

	protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV ֧��

// ʵ��
protected:
	DECLARE_MESSAGE_MAP()
};

CAboutDlg::CAboutDlg() : CDialog(CAboutDlg::IDD)
{
}

void CAboutDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
}

BEGIN_MESSAGE_MAP(CAboutDlg, CDialog)
END_MESSAGE_MAP()


// CHkj_Character_RecognitionDlg �Ի���
//////////////////////////////////////////////////////////////////////////
long	CHkj_Character_RecognitionDlg::m_nPort=-1;
long	CHkj_Character_RecognitionDlg::m_iSaveIndex=0;
int		CHkj_Character_RecognitionDlg::m_iSaveInterval=10;
int		CHkj_Character_RecognitionDlg::m_iImgWidth=2560;
int		CHkj_Character_RecognitionDlg::m_iImgHeight=1440;
HWND	CHkj_Character_RecognitionDlg::m_hPlayWnd=NULL;
cv::Mat		CHkj_Character_RecognitionDlg::m_cameraMatrix=cv::Mat();
cv::Mat		CHkj_Character_RecognitionDlg::m_distCoeffs=cv::Mat();
cv::Mat		CHkj_Character_RecognitionDlg::m_newMatrix=cv::Mat();
cv::Rect	CHkj_Character_RecognitionDlg::m_rectRoi=cv::Rect();
long		CHkj_Character_RecognitionDlg::m_iImageSaveIndex[8]={0};
CString		CHkj_Character_RecognitionDlg::m_iImageSavePath[8]={0};

CHkj_Character_RecognitionDlg::CHkj_Character_RecognitionDlg(CWnd* pParent /*=NULL*/)
	: CDialog(CHkj_Character_RecognitionDlg::IDD, pParent)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
	m_bIsPlaying=false;
	m_iCurChanIndex=-1;
}

void CHkj_Character_RecognitionDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	DDX_Control(pDX, IDC_TREE_CAMERA, m_treeCtrl_Camera);
	DDX_Control(pDX, IDC_COMBO_PIC_TYPE, m_comboPicType);
}

BEGIN_MESSAGE_MAP(CHkj_Character_RecognitionDlg, CDialog)
	ON_WM_SYSCOMMAND()
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	//}}AFX_MSG_MAP
	ON_NOTIFY(NM_DBLCLK, IDC_TREE_CAMERA, &CHkj_Character_RecognitionDlg::OnNMDblclkTreeCamera)
	ON_BN_CLICKED(IDC_BUTTON_CAPTURE, &CHkj_Character_RecognitionDlg::OnBnClickedButtonCapture)
	ON_WM_CLOSE()
END_MESSAGE_MAP()


// CHkj_Character_RecognitionDlg ��Ϣ�������

BOOL CHkj_Character_RecognitionDlg::OnInitDialog()
{
	CDialog::OnInitDialog();

	// ��������...���˵�����ӵ�ϵͳ�˵��С�

	// IDM_ABOUTBOX ������ϵͳ���Χ�ڡ�
	ASSERT((IDM_ABOUTBOX & 0xFFF0) == IDM_ABOUTBOX);
	ASSERT(IDM_ABOUTBOX < 0xF000);

	CMenu* pSysMenu = GetSystemMenu(FALSE);
	if (pSysMenu != NULL)
	{
		CString strAboutMenu;
		strAboutMenu.LoadString(IDS_ABOUTBOX);
		if (!strAboutMenu.IsEmpty())
		{
			pSysMenu->AppendMenu(MF_SEPARATOR);
			pSysMenu->AppendMenu(MF_STRING, IDM_ABOUTBOX, strAboutMenu);
		}
	}

	// ���ô˶Ի����ͼ�ꡣ��Ӧ�ó��������ڲ��ǶԻ���ʱ����ܽ��Զ�
	//  ִ�д˲���
	SetIcon(m_hIcon, TRUE);			// ���ô�ͼ��
	SetIcon(m_hIcon, FALSE);		// ����Сͼ��

	// TODO: �ڴ���Ӷ���ĳ�ʼ������
	//����
	CString strTime=L"";
	CTime CurTime = CTime::GetCurrentTime();
	strTime.Format(L"%04d-%02d-%02d %02d:%02d:%02d",CurTime.GetYear(),CurTime.GetMonth(),CurTime.GetDay(),CurTime.GetHour(),CurTime.GetMinute(),CurTime.GetSecond());
	CString strTitle=L"";
	strTitle.Format(L"�ϸ��а峧����ʶ�����---����ʼ����ʱ��Ϊ��%s  �������Ƽ���ѧ����о�Ժ���޹�˾��",strTime);
	SetWindowText(strTitle);

	m_comboPicType.SetCurSel(1);

	CString strInfo=L"";
	NET_DVR_Init();
	bool bIsLoadSuccess=LoadConfigFile(L"Hkj_Character_Recognition.xml");
	if (true==bIsLoadSuccess)
	{
		m_LogOper.AddLogInfo(L"Normal>> �����ļ���ȡ�ɹ�!");
	}
	else
	{
		m_LogOper.AddLogInfo(L"Error>> �����ļ���ȡʧ��!");
		return FALSE;
	}
	for(int i=0;i<m_ConfigCameraSet.iItemNum;i++)
	{
		m_ConfigCameraSet.Items[i].iCamID=ConnectCamera(m_ConfigCameraSet.Items[i].strIP,m_ConfigCameraSet.Items[i].iPort,m_ConfigCameraSet.Items[i].strUserName,m_ConfigCameraSet.Items[i].strPassword);
		if (m_ConfigCameraSet.Items[i].iCamID>=0)
		{
			strInfo.Format(L"Normal>> ���%d���ӳɹ�!",i);
			m_LogOper.AddLogInfo(strInfo);
		}
		else
		{
			strInfo.Format(L"Error>> ���%d����ʧ��!",i);
			m_LogOper.AddLogInfo(strInfo);
			//NET_DVR_Cleanup();
			//return FALSE;
		}
	}		
	CreateDeviceTree();

	CHkj_Character_RecognitionDlg::GetCameraMatrix();
	for(int i=0;i<m_ConfigCameraSet.iItemNum;i++)
	{
		if(true==m_ConfigCameraSet.Items[i].bIsAutoSave)
		{
			//EnterCallback(m_ConfigCameraSet.Items[i].iCamID);
			m_iImageSavePath[i]=L"";
			m_iImageSavePath[i].Format(L"%s",m_ConfigCameraSet.Items[i].strImgPath);
			m_hThread[i].m_ThreadParam.hWnd=m_hWnd;
			m_hThread[i].m_ThreadParam.nData=0;
			m_hThread[i].m_ThreadParam.index=m_ConfigCameraSet.Items[i].iCamNo*100+m_ConfigCameraSet.Items[i].iCamID;
			m_hThread[i].m_ThreadParam.bExit=false;
			m_hThread[i].m_ThreadParam.pMutex = new CMutex();
			m_hThread[i].BeginThread(ThreadProc);
			m_hThread[i].ResumeThread();
		}
	}

	return TRUE;  // ���ǽ��������õ��ؼ������򷵻� TRUE
}

UINT CHkj_Character_RecognitionDlg::ThreadProc(LPVOID pParam)
{
	ThreadParam* pThreadParam = (ThreadParam*)pParam;
	while (!pThreadParam->bExit)
	{		
		LONG lCamNO=pThreadParam->index/100;
		LONG lUserID=pThreadParam->index%100;
		switch(lCamNO)
		{
		case 0:
			GetCameraImageLoop(lCamNO,lUserID);
			pThreadParam->bExit=true;
			break;
		case 1:
			GetCameraImageLoop(lCamNO,lUserID);
			pThreadParam->bExit=true;
			break;
		case 2:
			GetCameraImageLoop(lCamNO,lUserID);
			pThreadParam->bExit=true;
			break;
		case 3:
			GetCameraImageLoop(lCamNO,lUserID);
			pThreadParam->bExit=true;
			break;
		default:break;
		}		
		Sleep(500);
		//
	}
	return 0;
}

void CHkj_Character_RecognitionDlg::OnSysCommand(UINT nID, LPARAM lParam)
{
	if ((nID & 0xFFF0) == IDM_ABOUTBOX)
	{
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	}
	else
	{
		CDialog::OnSysCommand(nID, lParam);
	}
}

// �����Ի��������С����ť������Ҫ����Ĵ���
//  �����Ƹ�ͼ�ꡣ����ʹ���ĵ�/��ͼģ�͵� MFC Ӧ�ó���
//  �⽫�ɿ���Զ���ɡ�

void CHkj_Character_RecognitionDlg::OnPaint()
{
	if (IsIconic())
	{
		CPaintDC dc(this); // ���ڻ��Ƶ��豸������

		SendMessage(WM_ICONERASEBKGND, reinterpret_cast<WPARAM>(dc.GetSafeHdc()), 0);

		// ʹͼ���ڹ����������о���
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// ����ͼ��
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

//���û��϶���С������ʱϵͳ���ô˺���ȡ�ù��
//��ʾ��
HCURSOR CHkj_Character_RecognitionDlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}

char*  CHkj_Character_RecognitionDlg::WideCharToMultiChar(CString str)
{
    string return_value;
    int len=WideCharToMultiByte(CP_ACP,0,str,str.GetLength(),NULL,0,NULL,NULL);
    char *buffer=new char[len+1];
    WideCharToMultiByte(CP_ACP,0,str,str.GetLength(),buffer,len,NULL,NULL);
    buffer[len]='\0';
    return buffer;
}

bool CHkj_Character_RecognitionDlg::LoadConfigFile(CString strPath)
{
	//��ȡӦ�ó���·��
	TCHAR szFileName[MAX_PATH];
	::GetModuleFileName(NULL, szFileName, MAX_PATH);
	CString strFileName = szFileName;
	int nIndex = strFileName.ReverseFind('\\');
	CString strAppPath = strFileName.Left(nIndex);
	CString strConfigName;

	m_LogOper.SetLogFilePath(strAppPath);

	strConfigName.Format(L"%s\\%s",strAppPath,strPath);
	HFile_xml hFileXml;
	int iJudge=hFileXml.LoadFile(strConfigName);
	if(1==iJudge)
	{
		CString strValue;

		hFileXml.Read(L"//�ַ�ʶ��ϵͳ��������//��������//�������",strValue);
		m_iCameraNum=_ttoi(strValue);
		
		m_ConfigCameraSet.iItemNum=0;
		for(int i=0;i<m_iCameraNum;i++)
		{
			CString strKey;

			strKey.Format(L"//�ַ�ʶ��ϵͳ��������//�ɼ��������//���%d//�����",i);
			hFileXml.Read(strKey,strValue);
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].iCamNo=_ttoi(strValue);

			strKey.Format(L"//�ַ�ʶ��ϵͳ��������//�ɼ��������//���%d//IP��ַ",i);
			hFileXml.Read(strKey,strValue);
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].strIP=L"";
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].strIP.Format(L"%s",strValue);

			strKey.Format(L"//�ַ�ʶ��ϵͳ��������//�ɼ��������//���%d//�˿ں�",i);
			hFileXml.Read(strKey,strValue);
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].iPort=_ttoi(strValue);

			strKey.Format(L"//�ַ�ʶ��ϵͳ��������//�ɼ��������//���%d//�û���",i);
			hFileXml.Read(strKey,strValue);
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].strUserName=L"";
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].strUserName.Format(L"%s",strValue);

			strKey.Format(L"//�ַ�ʶ��ϵͳ��������//�ɼ��������//���%d//����",i);
			hFileXml.Read(strKey,strValue);
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].strPassword=L"";
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].strPassword.Format(L"%s",strValue);

			strKey.Format(L"//�ַ�ʶ��ϵͳ��������//�ɼ��������//���%d//�Զ��洢",i);
			hFileXml.Read(strKey,strValue);
			if(_ttoi(strValue)>0)
			{
				m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].bIsAutoSave=true;
			}
			else
			{
				m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].bIsAutoSave=false;
			}

			strKey.Format(L"//�ַ�ʶ��ϵͳ��������//�ɼ��������//���%d//ͼ��洢·��",i);
			hFileXml.Read(strKey,strValue);
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].strImgPath=L"";
			m_ConfigCameraSet.Items[m_ConfigCameraSet.iItemNum].strImgPath.Format(L"%s",strValue);

			m_ConfigCameraSet.iItemNum++;
		}
		return true;
	}
	else
	{
		return false;
	}
}

long CHkj_Character_RecognitionDlg::ConnectCamera(CString strIP,int iPort,CString strUser,CString strPWD)
{		
	NET_DVR_SetConnectTime(2000, 1);
    NET_DVR_SetReconnect(10000, true);

	NET_DVR_DEVICEINFO_V30 DeviceInfoTmp;
	memset(&DeviceInfoTmp,0,sizeof(NET_DVR_DEVICEINFO_V30));
	
	char* cstrIP = WideCharToMultiChar(strIP);
	char* cstrUser = WideCharToMultiChar(strUser);
	char* cstrPWD = WideCharToMultiChar(strPWD);
	LONG lLoginID = NET_DVR_Login_V30(cstrIP,iPort,cstrUser,cstrPWD,&DeviceInfoTmp);
		
	delete[] cstrIP;
	delete[] cstrUser;
	delete[] cstrPWD;
	return lLoginID;
}


void CHkj_Character_RecognitionDlg::CreateDeviceTree()
{
	m_hDevItem = m_treeCtrl_Camera.InsertItem(L"�����豸");
	m_treeCtrl_Camera.SetItemData(m_hDevItem,DEVICETYPE*1000);
	for(int i=0; i<m_ConfigCameraSet.iItemNum; i++)
	{
		HTREEITEM ChanItem = m_treeCtrl_Camera.InsertItem(m_ConfigCameraSet.Items[i].strIP,m_hDevItem);
		m_treeCtrl_Camera.SetItemData(ChanItem,CHANNELTYPE*1000+i);   //Data��Ӧͨ���������е�����
	}
	m_treeCtrl_Camera.Expand(m_hDevItem,TVE_EXPAND);
}

void CHkj_Character_RecognitionDlg::OnNMDblclkTreeCamera(NMHDR *pNMHDR, LRESULT *pResult)
{
	// TODO: �ڴ���ӿؼ�֪ͨ����������
	HTREEITEM hSelected = m_treeCtrl_Camera.GetSelectedItem();
	
	if(NULL == hSelected)
	{
		return;
	}
	DWORD itemData = m_treeCtrl_Camera.GetItemData(hSelected);
	HTREEITEM hParent = NULL;
	int itype = itemData/1000;    //
	int iIndex = itemData%1000;

	switch(itype)
	{
	case DEVICETYPE:
		m_iCurChanIndex = -1;
		break;
	case CHANNELTYPE:
		m_iCurChanIndex = iIndex;
        PlayCameraChannel(m_iCurChanIndex);
		break;
	default:
		break;
	}

	*pResult = 0;
}

void CHkj_Character_RecognitionDlg::PlayCameraChannel(int Index)
{
 
	if(!m_bIsPlaying)
	{
		StartPlay(Index);
	}
	else
	{
        StopPlay();
		StartPlay(Index);
	}
}
//
void CHkj_Character_RecognitionDlg::SaveImage(CString strImgPath,int iIndex)
{
	char* cstrFilePath = WideCharToMultiChar(strImgPath);
	char strfilename[256]={0};
	sprintf(strfilename,"%s\\%d.jpg",cstrFilePath,iIndex);
	//NET_DVR_CapturePicture(m_lPlayHandle,strfilename);
	NET_DVR_JPEGPARA JpgPara = {0};
    JpgPara.wPicSize = 6;
	JpgPara.wPicQuality = 0;
	NET_DVR_CaptureJPEGPicture(m_ConfigCameraSet.Items[0].iCamID, 1, &JpgPara, strfilename);
}
//
void CHkj_Character_RecognitionDlg::StartPlay(int iIndex)
{
	NET_DVR_CLIENTINFO ClientInfo;
	ClientInfo.hPlayWnd     = GetDlgItem(IDC_STATIC_PLAY)->m_hWnd;
	ClientInfo.lChannel     = 1;
	ClientInfo.lLinkMode    = 0;
    ClientInfo.sMultiCastIP = NULL;
	m_lShowPlayHandle = NET_DVR_RealPlay_V30(m_ConfigCameraSet.Items[iIndex].iCamID,&ClientInfo,NULL,NULL,TRUE);

	if(-1 == m_lShowPlayHandle)
	{
		DWORD err=NET_DVR_GetLastError();
		CString strErr;
        strErr.Format(L"Error>> ���ų����������%d",err);
		m_LogOper.AddLogInfo(strErr);
		//NET_DVR_Cleanup();
		MessageBox(strErr);
		m_bIsPlaying = false;
	}
	else
	{
		m_bIsPlaying = true;
	}
}
//
void CHkj_Character_RecognitionDlg::StopPlay()
{
	if(m_lShowPlayHandle != -1)
	{
		NET_DVR_StopRealPlay(m_lShowPlayHandle);
		m_lShowPlayHandle=-1;
		m_bIsPlaying = FALSE;
	}
}
//
void CHkj_Character_RecognitionDlg::EnterCallback(int iIndex)
{
	NET_DVR_CLIENTINFO ClientInfo;
	ClientInfo.hPlayWnd     = NULL;
	ClientInfo.lChannel     = 1;
	ClientInfo.lLinkMode    = 0;
    ClientInfo.sMultiCastIP = NULL;
	m_lPlayHandle = NET_DVR_RealPlay_V30(m_ConfigCameraSet.Items[iIndex].iCamID,&ClientInfo,&fRealDataCallBack,NULL,TRUE);

	if(-1 == m_lPlayHandle)
	{
		DWORD err=NET_DVR_GetLastError();
		CString strErr;
        strErr.Format(L"Error>> ���ų����������%d",err);
		m_LogOper.AddLogInfo(strErr);
		//NET_DVR_Cleanup();
	}	
}
//
void CHkj_Character_RecognitionDlg::OnBnClickedButtonCapture()
{
	// TODO: �ڴ���ӿؼ�֪ͨ����������
	if(m_lShowPlayHandle == -1)
	{
        MessageBox(L"����ѡ��һ��ͨ������");
		return;
	}
	UpdateData(TRUE);

	char PicName[256] = {0};
	
	int iPicType = m_comboPicType.GetCurSel();
	if(0 == iPicType)  //bmp
	{
		CTime CurTime = CTime::GetCurrentTime();;
		sprintf(PicName,"%04d%02d%02d%02d%02d%02d.bmp",CurTime.GetYear(),CurTime.GetMonth(),CurTime.GetDay(),CurTime.GetHour(),CurTime.GetMinute(),CurTime.GetSecond()); 
		NET_DVR_CapturePicture(m_lShowPlayHandle,PicName);
	}
	else if(1 == iPicType)  //jgp
	{
		CTime CurTime = CTime::GetCurrentTime();;
		sprintf(PicName,"%04d%02d%02d%02d%02d%02d.jpg",CurTime.GetYear(),CurTime.GetMonth(),CurTime.GetDay(),CurTime.GetHour(),CurTime.GetMinute(),CurTime.GetSecond());
    
		//�齨jpg�ṹ
		NET_DVR_JPEGPARA JpgPara = {0};
        JpgPara.wPicSize = 6;
		JpgPara.wPicQuality = 0;

		NET_DVR_CaptureJPEGPicture(m_ConfigCameraSet.Items[m_iCurChanIndex].iCamID, 1, &JpgPara, PicName);
	}
	
	return;	
}

bool CHkj_Character_RecognitionDlg::GetCameraImageLoop(LONG lCamNO,LONG lUserID)
{
	NET_DVR_JPEGPARA JpegPara;
    JpegPara.wPicQuality=0;
    JpegPara.wPicSize=0xff;

	int iWidth=2560;
	int iHeight=1440;
	DWORD len = iHeight*iWidth;
	DWORD  SizeReturned=0;
	char *JpegPicBuffer= new char[len];
      
	while(true)
	{
		BOOL bRet= NET_DVR_CaptureJPEGPicture_NEW(lUserID, 1,&JpegPara,JpegPicBuffer,len,&SizeReturned);
		if (bRet)
		{
			cv::Mat img(iHeight, iWidth, CV_8UC1, (uchar*)JpegPicBuffer);
			cv::Mat src = imdecode(img,1);
			cv::Mat dst;
			CHkj_Character_RecognitionDlg::RectifyImage(src,dst);
			cv::Mat gray;
			cv::cvtColor(dst,gray,cv::COLOR_RGB2GRAY);
			//�ж��Ƿ��иְ�
			cv::Mat roi_top,gray_th_top;
			cv::Rect rect_top((int)(gray.cols*0.25),(int)(gray.rows*0.1),(int)(gray.cols*0.5),(int)(gray.rows*0.2));
			gray(rect_top).copyTo(roi_top);
			cv::threshold(roi_top,gray_th_top,50,255,1);

			cv::Mat roi_center,gray_th_center;
			cv::Rect rect_center((int)(gray.cols*0.25),(int)(gray.rows*0.4),(int)(gray.cols*0.5),(int)(gray.rows*0.2));
			gray(rect_center).copyTo(roi_center);
			cv::threshold(roi_center,gray_th_center,50,255,1);

			cv::Mat roi_bottom,gray_th_bottom;
			cv::Rect rect_bottom((int)(gray.cols*0.25),(int)(gray.rows*0.7),(int)(gray.cols*0.5),(int)(gray.rows*0.2));
			gray(rect_bottom).copyTo(roi_bottom);
			cv::threshold(roi_bottom,gray_th_bottom,50,255,1);

			float top_n=cv::countNonZero(gray_th_top); 
			float center_n=cv::countNonZero(gray_th_center); 
			float bottom_n=cv::countNonZero(gray_th_bottom); 
			
			float f_top_noZero=top_n/(gray_th_top.rows*gray_th_top.cols);
			float f_center_noZero=center_n/(gray_th_center.rows*gray_th_center.cols);
			float f_bottom_noZero=bottom_n/(gray_th_bottom.rows*gray_th_bottom.cols);

			//cv::imshow("ss",gray_th_center);
			//cv::waitKey();
			//
			if(f_top_noZero<0.01 || f_center_noZero<0.01 || f_bottom_noZero<0.01)
			{
				
				CString strAppPath=GetAppPath();
				CString strSaveImgPath=L"";
				strSaveImgPath.Format(L"%s\\CameraImg_src",m_iImageSavePath[lCamNO]);
				CreateDirectory(strSaveImgPath, NULL);
				//CHkj_Character_RecognitionDlg::SaveImageOpenCV(src,strSaveImgPath,m_iImageSaveIndex[lCamNO]);
				strSaveImgPath.Format(L"%s\\CameraImg_ref",m_iImageSavePath[lCamNO]);
				CreateDirectory(strSaveImgPath, NULL);
				CHkj_Character_RecognitionDlg::SaveImageOpenCV(dst,strSaveImgPath,m_iImageSaveIndex[lCamNO]);
				m_iImageSaveIndex[lCamNO]=m_iImageSaveIndex[lCamNO]+1;
			}
		}
		else
		{
			continue;
		}
		Sleep(100);
	}
	delete JpegPicBuffer;
	return true;
}

bool CHkj_Character_RecognitionDlg::GetCameraImage(LONG& lUserID)
{
	NET_DVR_JPEGPARA JpegPara;
    JpegPara.wPicQuality=0;
    JpegPara.wPicSize=0xff;

	int iWidth=2560;
	int iHeight=1440;
	DWORD len = iHeight*iWidth*2;
	char *JpegPicBuffer= new char[len];
      
	char filename[100];
	FILE *file=NULL;
	DWORD  SizeReturned=0;	
	BOOL bRet= NET_DVR_CaptureJPEGPicture_NEW(lUserID, 1,&JpegPara,JpegPicBuffer,len,&SizeReturned);
	if (bRet)
	{
		sprintf(filename,"JPEG_%d.jpg",0);
		file = fopen(filename,"wb");
		fwrite(JpegPicBuffer,SizeReturned,1,file);
		fclose(file);		
		delete JpegPicBuffer;
		return true;
	}
	else
	{
		delete JpegPicBuffer;
		return false;
	}	
}

CString CHkj_Character_RecognitionDlg::GetAppPath() 
{
	TCHAR szAppName[MAX_PATH];
	::GetModuleFileName(NULL, szAppName, MAX_PATH);
	CString strAppName = szAppName;
	int nIndex = strAppName.ReverseFind('\\');
	CString strAppPath = strAppName.Left(nIndex);
	return strAppPath;
}

void CHkj_Character_RecognitionDlg::GetCameraMatrix() 
{
	m_cameraMatrix = cv::Mat::eye(3, 3, CV_64F);
    m_cameraMatrix.at<double>(0, 0) = 1996.731;
    m_cameraMatrix.at<double>(0, 1) = 0;
    m_cameraMatrix.at<double>(0, 2) = 1301.808;
	m_cameraMatrix.at<double>(1, 0) = 0;
    m_cameraMatrix.at<double>(1, 1) = 1997.605;
    m_cameraMatrix.at<double>(1, 2) = 669.558;
	m_cameraMatrix.at<double>(2, 0) = 0;
    m_cameraMatrix.at<double>(2, 1) = 0;
    m_cameraMatrix.at<double>(2, 2) = 1;
 
	m_distCoeffs = cv::Mat::zeros(5, 1, CV_64F);
    m_distCoeffs.at<double>(0, 0) = -0.394368;
    m_distCoeffs.at<double>(1, 0) = 0.142365;
    m_distCoeffs.at<double>(2, 0) = 0.000733;
    m_distCoeffs.at<double>(3, 0) = 0.001086;
    m_distCoeffs.at<double>(4, 0) = -0.014611;

	cv::Size imageSize=cv::Size(m_iImgWidth,m_iImgHeight);
	m_newMatrix=cv::getOptimalNewCameraMatrix(m_cameraMatrix,m_distCoeffs,imageSize,1,imageSize,&m_rectRoi);
}

void CHkj_Character_RecognitionDlg::RectifyImage(cv::Mat src ,cv::Mat& dst) 
{
	cv::Mat dst_temp;
	cv::undistort(src,dst_temp,m_cameraMatrix,m_distCoeffs,m_newMatrix);
	dst_temp(m_rectRoi).copyTo(dst);
}

void CHkj_Character_RecognitionDlg::SaveImageOpenCV(cv::Mat src ,CString strImgPath, long iIndex) 
{
	string filename=CStringA(strImgPath);
	char strfilename[128];
	sprintf(strfilename,"\\%08d.jpg",iIndex);
	filename+=strfilename;
	IplImage* image=&(IplImage)src;
	const char* p=filename.data();
	cvSaveImage(p,image);
}

void CALLBACK CHkj_Character_RecognitionDlg::DecCBFun(long nPort,char * pBuf,long nSize,FRAME_INFO * pFrameInfo, long nReserved1,long nReserved2)
{
 	long lFrameType = pFrameInfo->nType;	
	if (lFrameType ==T_AUDIO16)
	{
		return;
	}
	else if(lFrameType ==T_YV12)
	{		
		m_iSaveInterval=m_iSaveInterval-1;
		if(m_iSaveInterval<=0)
		{
			m_iSaveInterval=10;
			m_iSaveIndex=m_iSaveIndex+1;
			cv::Mat src(pFrameInfo->nHeight, pFrameInfo->nWidth, CV_8UC1, (uchar*)pBuf);
			CString strAppPath=GetAppPath();
			CString strSaveImgPath=L"";
			strSaveImgPath.Format(L"%s\\CameraImg_%d",strAppPath,1);
			CreateDirectory(strSaveImgPath, NULL);
			//cv::Mat dst;
			//RectifyImage(src,dst);
			SaveImageOpenCV(src,strSaveImgPath,m_iSaveIndex);
		}
	}
}

void CALLBACK CHkj_Character_RecognitionDlg::fRealDataCallBack(LONG lRealHandle,DWORD dwDataType,BYTE *pBuffer,DWORD dwBufSize,void *pUser)
{
	DWORD dRet = 0;
	BOOL inData = FALSE;

	switch (dwDataType)
	{
	case NET_DVR_SYSHEAD:
		if (!PlayM4_GetPort(&m_nPort))
		{
			break;
		}
		if (!PlayM4_OpenStream(m_nPort,pBuffer,dwBufSize,1024*1024))
		{
			dRet=PlayM4_GetLastError(m_nPort);
			break;
		}
	
 		if (!PlayM4_SetDecCallBack(m_nPort,DecCBFun))//���ý���ص����� ֻ���벻��ʾ
 		{
 			dRet=PlayM4_GetLastError(m_nPort);
 			break;
 		}
			
		//if (!PlayM4_SetDecCallBackEx(nPort,DecCBFun,NULL,NULL))//���ý���ص����� ��������ʾ
		//{
		//	dRet=PlayM4_GetLastError(nPort);
		//	break;
		//}

		if (!PlayM4_Play(m_nPort,m_hPlayWnd))//����Ƶ����
		{
			dRet=PlayM4_GetLastError(m_nPort);
			break;
		}
		
		//if (!PlayM4_PlaySound(nPort))//����Ƶ����, ��Ҫ�����Ǹ�����
		//{
		//	dRet=PlayM4_GetLastError(nPort);
		//	break;
		//}
		break;
		
	case NET_DVR_STREAMDATA:
        inData=PlayM4_InputData(m_nPort,pBuffer,dwBufSize);
		while (!inData)
		{
			Sleep(10);
			inData=PlayM4_InputData(m_nPort,pBuffer,dwBufSize);	
		}
		break;
	default:
		inData=PlayM4_InputData(m_nPort,pBuffer,dwBufSize);
		while (!inData)
		{
			Sleep(10);
			inData=PlayM4_InputData(m_nPort,pBuffer,dwBufSize);	
		}
		break;
	}
}


void CHkj_Character_RecognitionDlg::OnClose()
{
	// TODO: �ڴ������Ϣ�����������/�����Ĭ��ֵ
	NET_DVR_Cleanup();
	UINT nRet=MessageBox(_T(">>�Ƿ��˳����ʶ��ϵͳ��\n>>�����ѡ��!"),_T("��ʾ��Ϣ"),MB_YESNO);
	if(nRet == IDYES)
	{
		m_LogOper.AddLogInfo(L"�˳����ʶ��ϵͳ��");
		HANDLE hself=GetCurrentProcess();
		TerminateProcess(hself,0);
	}
	else
	{
		m_LogOper.AddLogInfo(L"ȡ����һ���˳����ʶ��ϵͳ��");
		return;
	}

	CDialog::OnClose();
}
