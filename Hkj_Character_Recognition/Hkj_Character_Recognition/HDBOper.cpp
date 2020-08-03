#include "StdAfx.h"
#include "HDBOper.h"

HDBOper::HDBOper(void)
{
	::CoInitializeEx(NULL, COINIT_MULTITHREADED);
	m_bConnected=false;
}

HDBOper::~HDBOper(void)
{
	::CoUninitialize();
}

//-----------------------------------------------------------
//描述：连接数据库
bool   HDBOper::ConnectDB(CString strDBServer, CString strDBName, CString strUser, CString strPassWd, CString strType)
{
	m_pConnection.CreateInstance(__uuidof(Connection));
	CString strConnect;
	strConnect.Format(L"Provider=SQLOLEDB.1;Password=%s;Persist Security Info=True; User ID=%s;Initial Catalog=%s;Data Source=%s",strPassWd,strUser,strDBName,strDBServer);

	m_pConnection->CursorLocation = adUseClient;
	m_pConnection->Open(_bstr_t( strConnect), L"", L"", -1);
	
	m_pCommand.CreateInstance(__uuidof(Command));
	m_pCommand->ActiveConnection = m_pConnection;
	m_pCommand->CommandType = adCmdText;
	m_pSearchSet.CreateInstance(__uuidof(Recordset));	

	m_bConnected = true;

	return true;
}

bool   HDBOper::SearchDefect(SteelDefectInfoSet& DefectSet,long& iDefectMaxIndex,CString strSQLCondition)
{
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pSearchSet->Open((_variant_t)strSQLCondition,_variant_t((IDispatch *)m_pConnection,true),adOpenDynamic,adLockPessimistic,adCmdText);
	long lRecordCount = m_pSearchSet->GetRecordCount();
	DefectSet.iItemNum=0;
	if(lRecordCount > 0) 
	{
		m_pSearchSet->MoveFirst();
		int iRecordIndex = 0;
		while(!m_pSearchSet->adoEOF)
		{
			_variant_t Value;		
			Value = m_pSearchSet->GetCollect("DefectNo");
			DefectSet.Items[DefectSet.iItemNum].iDefectNo=Value.intVal;
			if(DefectSet.Items[DefectSet.iItemNum].iDefectNo>iDefectMaxIndex)
			{
				iDefectMaxIndex=DefectSet.Items[DefectSet.iItemNum].iDefectNo;
			}
				
			Value = m_pSearchSet->GetCollect("SteelNo");
			DefectSet.Items[DefectSet.iItemNum].iSteelNo=Value.intVal;

			Value = m_pSearchSet->GetCollect("CameraNo");
			DefectSet.Items[DefectSet.iItemNum].iCameraNo=Value.iVal;

			Value = m_pSearchSet->GetCollect("ImageIndex");
			DefectSet.Items[DefectSet.iItemNum].iImageIndex=Value.iVal;

			Value = m_pSearchSet->GetCollect("Class");
			DefectSet.Items[DefectSet.iItemNum].iClass=Value.iVal;
			DefectSet.Items[DefectSet.iItemNum].iPerClass=0;

			Value = m_pSearchSet->GetCollect("Grade");
			DefectSet.Items[DefectSet.iItemNum].iGrade=Value.iVal;

			Value = m_pSearchSet->GetCollect("LeftInImg");
			DefectSet.Items[DefectSet.iItemNum].iLeftInImg=Value.iVal;

			Value = m_pSearchSet->GetCollect("RightInImg");
			DefectSet.Items[DefectSet.iItemNum].iRightInImg=Value.iVal;

			Value = m_pSearchSet->GetCollect("TopInImg");
			DefectSet.Items[DefectSet.iItemNum].iTopInImg=Value.iVal;

			Value = m_pSearchSet->GetCollect("BottomInImg");
			DefectSet.Items[DefectSet.iItemNum].iBottomInImg=Value.iVal;

			Value = m_pSearchSet->GetCollect("Area");
			DefectSet.Items[DefectSet.iItemNum].iArea=Value.intVal;		

			m_pSearchSet->MoveNext();
			iRecordIndex++;
			DefectSet.iItemNum++;

			if(DefectSet.iItemNum>1024)
			{
				break;
			}
		}
	}

	m_pSearchSet->Close();
	return true;
}

bool   HDBOper::SearchDefectFromSteelNo_LimitLength(DefectAxisSet& tagDefectAxisSet,CString strSQLCondition,int iStartLenght,int *iLimitClass,int iDefectTableNo)
{
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pSearchSet->Open((_variant_t)strSQLCondition,_variant_t((IDispatch *)m_pConnection,true),adOpenDynamic,adLockPessimistic,adCmdText);
	long lRecordCount = m_pSearchSet->GetRecordCount();
	//tagDefectAxisSet.iItemNum=0;
	if(lRecordCount > 0) 
	{
		m_pSearchSet->MoveFirst();
		int iRecordIndex = 0;
		while(!m_pSearchSet->adoEOF)
		{
			_variant_t Value;	

			Value = m_pSearchSet->GetCollect("ID");
			long iID=Value.intVal;

			Value = m_pSearchSet->GetCollect("DefectNo");
			long iDefectNo=Value.intVal;

			Value = m_pSearchSet->GetCollect("Class");
			int iClass=Value.iVal;
			//缺陷横向位置
			Value = m_pSearchSet->GetCollect("LeftInSteel");
			int iLeftInsteel=Value.iVal;
			Value = m_pSearchSet->GetCollect("RightInSteel");
			int iRightInSteel=Value.iVal;
			//缺陷纵向位置
			Value = m_pSearchSet->GetCollect("TopInSteel");
			long iTopInSteel=Value.lVal;
			Value = m_pSearchSet->GetCollect("BottomInSteel");
			long iBottomInSteel=Value.lVal;
			long iYPosInSteel=(iTopInSteel+iBottomInSteel)/2;
			//长宽比
			//Value = m_pSearchSet->GetCollect("LeftInImg");
			//int iLeftInImg=Value.iVal;
			//Value = m_pSearchSet->GetCollect("RightInImg");
			//int iRightInImg=Value.iVal;
			//float	fWidth=abs(iRightInImg-iLeftInImg);
			//Value = m_pSearchSet->GetCollect("TopInImg");
			//long iTopInImg=Value.lVal;
			//Value = m_pSearchSet->GetCollect("BottomInImg");
			//long iBottomInImg=Value.lVal;
			//float	fHeight=abs(iBottomInImg-iTopInImg);
			//float fRidao=fHeight/(fWidth+0.1);
			//
			if(iYPosInSteel>iStartLenght )//&& fRidao<3设置从距头多少的位置开始统计缺陷 有浪形的时候设为150，没浪形时设为50;把长宽比大的去掉
			{
				//判断一次类别，如果类别为划伤和侧翻线就不参与周期检测了
				bool bIsNoLimitClass=true;
				for(int k=0;k<64;k++)
				{
					if(iLimitClass[k]==0 )
					{
						break;
					}
					else if(iClass==iLimitClass[k])
					{
						bIsNoLimitClass=false;
					}
				}
				if(true==bIsNoLimitClass) //排除划伤，侧翻线，水油印，铁鳞，裂边
				{			

					//利用坐标计算的纵向位置
					//Value = m_pSearchSet->GetCollect("ImageIndex");
					//long iImgIndex=Value.lVal;
					//Value = m_pSearchSet->GetCollect("TopInImg");
					//long iTopInSteel=Value.lVal;
					//Value = m_pSearchSet->GetCollect("BottomInImg");
					//long iBottomInSteel=Value.lVal;
					//tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iLongitudinalInSteel=iImgIndex*950+(iTopInSteel+iBottomInSteel)/2;

					tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iDBIDIndex=iID;
					tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iDefectNo=iDefectNo;
					tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iClass=iClass;
					tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iHorizontalInSteel=(iLeftInsteel+iRightInSteel)/2;
					tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iLongitudinalInSteel=(iTopInSteel+iBottomInSteel)/2;
					tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iIndex=tagDefectAxisSet.iItemNum;
					tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iFromDefectTableNo=iDefectTableNo;

					tagDefectAxisSet.iItemNum++;
					if(tagDefectAxisSet.iItemNum>5000)
					{
						break;
					}
				}
			}

			m_pSearchSet->MoveNext();
			iRecordIndex++;
		}
	}

	m_pSearchSet->Close();
	return true;
}

bool   HDBOper::SearchDefectFromSteelNo_AllLength(DefectAxisSet& tagDefectAxisSet,CString strSQLCondition,int iDefectTableNo)
{
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pSearchSet->Open((_variant_t)strSQLCondition,_variant_t((IDispatch *)m_pConnection,true),adOpenDynamic,adLockPessimistic,adCmdText);
	long lRecordCount = m_pSearchSet->GetRecordCount();
	//tagDefectAxisSet.iItemNum=0;
	if(lRecordCount > 0) 
	{
		m_pSearchSet->MoveFirst();
		int iRecordIndex = 0;
		while(!m_pSearchSet->adoEOF)
		{
			_variant_t Value;	

			Value = m_pSearchSet->GetCollect("ID");
			long iID=Value.intVal;
			
			Value = m_pSearchSet->GetCollect("DefectNo");
			long iDefectNo=Value.intVal;

			Value = m_pSearchSet->GetCollect("Class");
			int iClass=Value.iVal;
			//缺陷横向位置
			Value = m_pSearchSet->GetCollect("LeftInSteel");
			int iLeftInsteel=Value.iVal;
			Value = m_pSearchSet->GetCollect("RightInSteel");
			int iRightInSteel=Value.iVal;
			//缺陷纵向位置
			Value = m_pSearchSet->GetCollect("TopInSteel");
			long iTopInSteel=Value.lVal;
			Value = m_pSearchSet->GetCollect("BottomInSteel");
			long iBottomInSteel=Value.lVal;
			long iYPosInSteel=(iTopInSteel+iBottomInSteel)/2;
			//长宽比
			Value = m_pSearchSet->GetCollect("LeftInImg");
			int iLeftInImg=Value.iVal;
			Value = m_pSearchSet->GetCollect("RightInImg");
			int iRightInImg=Value.iVal;
			float	fWidth=abs(iRightInImg-iLeftInImg);
			Value = m_pSearchSet->GetCollect("TopInImg");
			long iTopInImg=Value.lVal;
			Value = m_pSearchSet->GetCollect("BottomInImg");
			long iBottomInImg=Value.lVal;
			float	fHeight=abs(iBottomInImg-iTopInImg);
			float fRidao=fHeight/(fWidth+0.1);
			//
			tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iDBIDIndex=iID;
			tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iDefectNo=iDefectNo;
			tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iClass=iClass;
			tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iHorizontalInSteel=(iLeftInsteel+iRightInSteel)/2;
			tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iLongitudinalInSteel=(iTopInSteel+iBottomInSteel)/2;
			tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iIndex=tagDefectAxisSet.iItemNum;
			tagDefectAxisSet.Items[tagDefectAxisSet.iItemNum].iFromDefectTableNo=iDefectTableNo;

			tagDefectAxisSet.iItemNum++;
			if(tagDefectAxisSet.iItemNum>5000)
			{
				break;
			}

			m_pSearchSet->MoveNext();
			iRecordIndex++;
		}
	}

	m_pSearchSet->Close();
	return true;
}

bool   HDBOper::GetDefectMaxNum(long& iDefectNoIndex,CString strSQLCondition)
{
	long iDefectNum = 0;
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pSearchSet->Open((_variant_t)strSQLCondition,_variant_t((IDispatch *)m_pConnection,true),adOpenDynamic,adLockPessimistic,adCmdText);
	long lRecordCount = m_pSearchSet->GetRecordCount();
	iDefectNum = lRecordCount;
	if(lRecordCount > 0) 
	{
		m_pSearchSet->MoveFirst();
		int iRecordIndex = 0;
		while(!m_pSearchSet->adoEOF)
		{
			_variant_t Value;		
			Value = m_pSearchSet->GetCollect("DefectNo");
			iDefectNoIndex=Value.intVal;
			m_pSearchSet->MoveNext();
		}
	}
	
	m_pSearchSet->Close();
	return true;
}

bool   HDBOper::GetDefectSumNum(long& iDefectSum,CString strSQLCondition)
{
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pSearchSet->Open((_variant_t)strSQLCondition,_variant_t((IDispatch *)m_pConnection,true),adOpenDynamic,adLockPessimistic,adCmdText);
	long lRecordCount = m_pSearchSet->GetRecordCount();
	if(lRecordCount > 0) 
	{
		m_pSearchSet->MoveFirst();
		int iRecordIndex = 0;
		while(!m_pSearchSet->adoEOF)
		{
			_variant_t Value;		
			Value = m_pSearchSet->GetCollect("countsum");
			iDefectSum=Value.lVal;
			m_pSearchSet->MoveNext();
			break;
		}
	}
	
	m_pSearchSet->Close();
	return true;
}

bool   HDBOper::GetNearSteelNo(long& iSteelNo,CString strSQLCondition)
{
	long iDefectNum = 0;
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pSearchSet->Open((_variant_t)strSQLCondition,_variant_t((IDispatch *)m_pConnection,true),adOpenDynamic,adLockPessimistic,adCmdText);
	long lRecordCount = m_pSearchSet->GetRecordCount();
	iDefectNum = lRecordCount;
	if(lRecordCount > 0) 
	{
		m_pSearchSet->MoveFirst();
		int iRecordIndex = 0;
		while(!m_pSearchSet->adoEOF)
		{
			_variant_t Value;		
			Value = m_pSearchSet->GetCollect("SequeceNo");
			iSteelNo=Value.lVal;

			Value = m_pSearchSet->GetCollect("BottomLen");
			long iSteelLen=Value.lVal;
			if(iSteelLen<=0)
			{
				iSteelNo=0;
			}
			m_pSearchSet->MoveNext();
		}
	}	
	m_pSearchSet->Close();
	return true;
}

bool   HDBOper::GetSteelLength(long iSteelNo,long& iLength,CString strSQLCondition)
{
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pSearchSet->Open((_variant_t)strSQLCondition,_variant_t((IDispatch *)m_pConnection,true),adOpenDynamic,adLockPessimistic,adCmdText);
	long lRecordCount = m_pSearchSet->GetRecordCount();
	if(lRecordCount > 0) 
	{
		m_pSearchSet->MoveFirst();
		while(!m_pSearchSet->adoEOF)
		{
			_variant_t Value;		
			Value = m_pSearchSet->GetCollect("Length");
			iLength=Value.lVal;

			m_pSearchSet->MoveNext();
		}
	}	
	m_pSearchSet->Close();
	return true;
}

bool   HDBOper::GetNearFinishSteelNo(long& iSteelNo,CString strSQLCondition)
{
	long iDefectNum = 0;
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pSearchSet->Open((_variant_t)strSQLCondition,_variant_t((IDispatch *)m_pConnection,true),adOpenDynamic,adLockPessimistic,adCmdText);
	long lRecordCount = m_pSearchSet->GetRecordCount();
	iDefectNum = lRecordCount;
	if(lRecordCount > 0) 
	{
		m_pSearchSet->MoveFirst();
		int iRecordIndex = 0;
		while(!m_pSearchSet->adoEOF)
		{
			_variant_t Value;		
			Value = m_pSearchSet->GetCollect("SequeceNo");
			iSteelNo=Value.lVal;

			Value = m_pSearchSet->GetCollect("BottomLen");
			long iSteelLen=Value.lVal;
			if(iSteelLen>0)
			{
				break;
			}
			m_pSearchSet->MoveNext();
		}
	}	
	m_pSearchSet->Close();
	return true;
}

bool   HDBOper::UpdateDefect(CString strSQLCondition)
{
	if(false == m_bConnected) 
	{
		return false;
	}			
	m_pCommand->CommandText = _bstr_t( strSQLCondition);
	m_pCommand->Execute(NULL, NULL, adCmdText);
	return true;
}