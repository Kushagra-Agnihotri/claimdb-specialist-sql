@echo off
cd /d "%~dp0"
title Tonight runner - DO NOT CLOSE
echo bat started %date% %time% > tonight_bat_check.txt
where python >> tonight_bat_check.txt 2>&1
where py >> tonight_bat_check.txt 2>&1
where ollama >> tonight_bat_check.txt 2>&1
powercfg /change standby-timeout-ac 0 >nul 2>&1
powercfg /change hibernate-timeout-ac 0 >nul 2>&1
python --version >> tonight_bat_check.txt 2>&1
if %errorlevel%==0 (
  echo using python >> tonight_bat_check.txt
  python runner.py
) else (
  echo using py >> tonight_bat_check.txt
  py -3 runner.py
)
echo runner ended with %errorlevel% >> tonight_bat_check.txt
pause
