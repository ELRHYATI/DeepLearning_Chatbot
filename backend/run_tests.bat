@echo off
REM Script to run tests on Windows
echo Running tests...
cd /d %~dp0

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run tests with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

echo.
echo Test coverage report generated in htmlcov/index.html
pause

