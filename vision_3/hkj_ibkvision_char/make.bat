@echo off
set libname=hkj_ibkvision_char
rem if exist build ( rd build /s /q )
python __build__.py build_ext --inplace
xcopy %libname% .\ /s /e /y
rd %libname% /s /q
del *.c /s /q
pause
