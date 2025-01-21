建議先開起虛擬環境：
建立方式：
python -m venv env
或是
python3 -m venv env

隨後開啟虛擬環境：
Linux:
source env/bin/activate
Windows:
# Windows CMD
env\Scripts\activate.bat
# PowerShell
env\Scripts\Activate.ps1

隨後安裝所需要的 python 模組：
pip install -r requirement.txt

創建 .enve，並依照格式填寫：
GEMINI_API_KEY = ""
CLAUDE_API_KEY = ""