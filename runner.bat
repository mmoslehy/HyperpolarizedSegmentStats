@echo off
rem if exist ".\backupenv.bat" del ".\backupenv.bat"
for /f "tokens=1* delims==" %%a in ('set') do (
rem echo set %%a=%%b>> .\backupenv.bat
set %%a=
)

for /f "usebackq tokens=1*" %%i in (`echo %*`) DO @ set params=%%j
%1 %params%
