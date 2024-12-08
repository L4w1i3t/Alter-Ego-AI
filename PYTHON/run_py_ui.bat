@echo off

REM Activate the virtual environment
CALL alter_ego\venv\Scripts\activate.bat

REM Set PATH explicitly for safety
SET PATH=alter_ego\venv\Scripts;%PATH%

REM Run the Python script
python alter_ego\__main__.py

REM Handle errors
IF %ERRORLEVEL% NEQ 0 (
    echo The application encountered an error.
    pause
)

REM Deactivate the virtual environment
deactivate
