#pragma once
// µº»Î ado ø‚ -----------------------------------------------------------
#pragma warning(disable:4146)
//#import "C:\Program Files\Common Files\System\ADO\msado15.dll" no_namespace rename("EOF","adoEOF"), rename("BOF","adoBOF") rename(L"LockTypeEnum", "adoLockTypeEnum") 
#import "C:\Program Files\Common Files\System\ADO\msado15.dll" no_namespace rename("EOF","adoEOF"), rename("BOF","adoBOF") rename(L"LockTypeEnum", "adoLockTypeEnum") 
#pragma warning(default:4146)

typedef struct tagSteelDefectInfo
{
	long iDefectNo;
	long iSteelNo;
	int iCameraNo;
	int iImageIndex;
	int iClass;
	int iPerClass;
	int iGrade;
	int iLeftInImg;
	int iRightInImg;
	int iTopInImg;
	int iBottomInImg;
	int iArea;
}SteelDefectInfo,*PSteelDefectInfo;
typedef struct tagSteelDefectInfoSet
{
	enum {MAX_ITEMNUM = 10240};
	SteelDefectInfo Items[MAX_ITEMNUM];
	int iItemNum;
}SteelDefectInfoSet,*PSteelDefectInfoSet;

typedef struct tagDefectAxis
{
	int iIndex;
	long iDBIDIndex;
	long iDefectNo;
	short int iFromDefectTableNo;
	short int iClass;
	int iHorizontalInSteel;
	long iLongitudinalInSteel;
}DefectAxis,*PDefectAxis;
typedef struct tagDefectAxisSet
{
	enum {MAX_ITEMNUM = 5000};
	DefectAxis Items[MAX_ITEMNUM];
	int iItemNum;
}DefectAxisSet,*PDefectAxisSet;

class HDBOper
{
public:
	HDBOper(void);
	~HDBOper(void);

	_ConnectionPtr			m_pConnection;
	_CommandPtr				m_pCommand;
	_RecordsetPtr			m_pSearchSet;

	bool					m_bConnected;
	
	bool   HDBOper::ConnectDB(CString strDBServer, CString strDBName, CString strUser, CString strPassWd, CString strType);
	bool   HDBOper::SearchDefect(SteelDefectInfoSet& DefectSet,long& iDefectMaxIndex,CString strSQLCondition);
	bool   HDBOper::SearchDefectFromSteelNo_LimitLength(DefectAxisSet& tagDefectAxisSet,CString strSQLCondition,int iStartLenght,int *iLimitClass,int iDefectTableNo);
	bool   HDBOper::SearchDefectFromSteelNo_AllLength(DefectAxisSet& tagDefectAxisSet,CString strSQLCondition,int iDefectTableNo);
	bool   HDBOper::GetDefectMaxNum(long& iDefectNoIndex,CString strSQLCondition);
	bool   HDBOper::GetDefectSumNum(long& iDefectSum,CString strSQLCondition);
	bool   HDBOper::GetNearSteelNo(long& iSteelNo,CString strSQLCondition);
	bool   HDBOper::GetNearFinishSteelNo(long& iSteelNo,CString strSQLCondition);
	bool   HDBOper::UpdateDefect(CString strSQLCondition);
	bool   HDBOper::GetSteelLength(long iSteelNo,long& iLength,CString strSQLCondition);
};
