@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Finding Python paths...
for /f "delims=" %%i in ('python -c "import sys; print(sys.base_exec_prefix)"') do set PYTHON_BASE=%%i

echo Building exe...
pyinstaller --onefile --windowed ^
  --name "FFXIV_OTP_Login" ^
  --hidden-import=win32crypt ^
  --hidden-import=pyotp ^
  --hidden-import=win32gui ^
  --hidden-import=win32con ^
  --hidden-import=win32process ^
  --hidden-import=win32api ^
  --hidden-import=pyzbar ^
  --hidden-import=PIL ^
  --collect-all tkinter ^
  --collect-all pyzbar ^
  --add-binary "%PYTHON_BASE%\DLLs\_tkinter.pyd;." ^
  --add-binary "%PYTHON_BASE%\DLLs\tcl86t.dll;." ^
  --add-binary "%PYTHON_BASE%\DLLs\tk86t.dll;." ^
  --add-data "%PYTHON_BASE%\tcl;tcl" ^
  main.py

echo Done! Output: dist\FFXIV_OTP_Login.exe
pause
