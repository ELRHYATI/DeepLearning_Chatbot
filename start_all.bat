@echo off
echo ========================================
echo   Starting French Academic AI Chatbot
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/4] Setting up backend...
if not exist backend (
    echo ERROR: Backend directory not found
    pause
    exit /b 1
)
cd backend
if not exist venv (
    echo Creating virtual environment...
    echo This may take a minute...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo [2/4] Installing backend dependencies (if needed)...
echo This may take several minutes, please wait...
echo.

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip --quiet >nul 2>&1

if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    echo This is a long process, please be patient...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo WARNING: Some dependencies may have failed to install
        echo Attempting to install core dependencies only...
        echo.
        pip install fastapi uvicorn[standard] pydantic sqlalchemy python-multipart python-dotenv aiofiles httpx accelerate python-jose[cryptography] passlib[bcrypt] email-validator
        pip install transformers datasets langchain langchain-community chromadb pypdf python-docx "numpy>=1.26.0"
        pip install torch --index-url https://download.pytorch.org/whl/cpu
        pip install redis celery rank-bm25 psutil 2>nul || echo Optional: redis, celery, rank-bm25, psutil skipped
        pip install language-tool-python 2>nul || echo Optional: language-tool-python skipped
    )
) else (
    echo Installing core dependencies...
    echo This is a long process, please be patient...
    echo.
    pip install fastapi uvicorn[standard] pydantic sqlalchemy python-multipart python-dotenv aiofiles httpx accelerate python-jose[cryptography] passlib[bcrypt] email-validator
    pip install transformers datasets langchain langchain-community chromadb pypdf python-docx "numpy>=1.26.0"
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install redis celery rank-bm25 psutil 2>nul || echo Optional: redis, celery, rank-bm25, psutil skipped
    pip install language-tool-python 2>nul || echo Optional: language-tool-python skipped
)
echo.
echo Backend dependencies installation completed!

echo [3/4] Starting backend server...
REM We're already in the backend directory, check venv relative to current directory
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found in backend directory
    echo Please run the script again to create it
    pause
    exit /b 1
)
set BACKEND_DIR=%~dp0backend
start "Backend Server" cmd /k "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate.bat && echo Backend starting on http://localhost:8000 && echo. && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak >nul

cd ..

echo [4/4] Starting frontend server...
set FRONTEND_DIR=%~dp0frontend
if not exist "%FRONTEND_DIR%" (
    echo ERROR: Frontend directory not found
    pause
    exit /b 1
)
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

start "Frontend Server" cmd /k "cd /d "%FRONTEND_DIR%" && echo Frontend starting on http://localhost:3000 && echo. && npm run dev"

cd ..

echo.
echo ========================================
echo   Servers Starting...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo NOTE: Redis and Celery are optional but recommended
echo       Install Redis separately if you want to use caching and async tasks
echo.
echo Press any key to open the application in your browser...
pause >nul

timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo ========================================
echo   Application opened in browser
echo ========================================
echo.
echo Servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
echo To stop all servers, close the Backend and Frontend windows.
echo.
pause

