@echo off
setlocal
cd /d D:\Pet
set "PET_PYTHON=%~1"
if not defined PET_PYTHON for /f "delims=" %%P in ('py -3.8-64 -c "import sys; print(sys.executable)"') do set "PET_PYTHON=%%P"
if not defined PET_PYTHON exit /b 1
"%PET_PYTHON%" -c "import sys,struct; assert sys.version_info[:3] == (3,8,10) and struct.calcsize('P') == 8, 'Requires CPython 3.8.10 x64'"
if errorlevel 1 exit /b 1
"%PET_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
set "PYINSTALLER_CONFIG_DIR=D:\Pet\cache_x64"
"%PET_PYTHON%" -m PyInstaller --noconfirm --clean --onefile --windowed --noupx ^
  --name Pet_x64 --add-data "D:\Pet\pet.png;." --add-data "D:\Pet\forms;forms" ^
  --distpath "D:\Pet" --workpath "D:\Pet\build_x64" --specpath "D:\Pet\spec_x64" main.py
exit /b %errorlevel%
