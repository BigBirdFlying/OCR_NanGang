// Hkj_Character_Recognition.h : PROJECT_NAME Ӧ�ó������ͷ�ļ�
//

#pragma once

#ifndef __AFXWIN_H__
	#error "�ڰ������ļ�֮ǰ������stdafx.h�������� PCH �ļ�"
#endif

#include "resource.h"		// ������


// CHkj_Character_RecognitionApp:
// �йش����ʵ�֣������ Hkj_Character_Recognition.cpp
//

class CHkj_Character_RecognitionApp : public CWinApp
{
public:
	CHkj_Character_RecognitionApp();

// ��д
	public:
	virtual BOOL InitInstance();

// ʵ��

	DECLARE_MESSAGE_MAP()
};

extern CHkj_Character_RecognitionApp theApp;