@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Building exe...
pyinstaller --onefile --windowed --name "FFXIV_OTP_Login" --hidden-import=win32crypt --hidden-import=pyotp --hidden-import=win32gui --hidden-import=win32con --hidden-import=win32process main.py

echo Done! Output: dist\FFXIV_OTP_Login.exe
pause
