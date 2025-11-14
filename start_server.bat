@echo off
REM EHR Web Application Startup Script
echo ======================================================================
echo EHR WEB APPLICATION - STARTUP SCRIPT
echo ======================================================================
echo.

REM Check if ffmpeg is installed
if not exist "ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg not found. Installing...
    python install_ffmpeg.py
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install ffmpeg
        echo Please run install_ffmpeg.py manually
        pause
        exit /b 1
    )
)

echo ✅ FFmpeg is ready
echo.
echo Starting Flask server...
echo Open your browser to: http://127.0.0.1:5000
echo.
echo Press CTRL+C to stop the server
echo ======================================================================
echo.

REM Start the Flask app with ffmpeg in PATH and no-reload flag
python app.py --no-reload
