@echo off
REM Meta-Project Windows One-Click Launch
echo [1/3] Setting up environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/3] Installing dependencies...
pip install -r requirements.txt

echo [3/3] Starting AI Code Review Assistant...
REM Start FastAPI in background
start /B uvicorn server.app:app --host 0.0.0.0 --port 7860

REM Start Streamlit
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
pause
