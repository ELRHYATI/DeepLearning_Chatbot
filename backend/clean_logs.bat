@echo off
REM Script to clean Java crash logs and other log files
echo Cleaning log files...

cd /d %~dp0

REM Delete Java crash logs
del /Q hs_err_pid*.log 2>nul
del /Q replay_pid*.log 2>nul

REM Delete other log files
del /Q *.log 2>nul

echo Log files cleaned!
pause

