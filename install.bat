@echo off
echo.
echo ====================================
echo   Stock POS AI Features Installer
echo ====================================
echo.

echo Installing base packages...
pip install -r requirements.txt

echo.
echo ====================================
echo   AI Service Selection
echo ====================================
echo.
echo 1. OpenAI (ChatGPT)
echo 2. Anthropic (Claude)
echo 3. Skip (use offline mode)
echo.

setlocal enabledelayedexpansion
set /p choice="Select an option (1-3): "

if "%choice%"=="1" (
    echo Installing OpenAI package...
    pip install openai
    echo Done! Remember to set your OpenAI API Key in the app.
) else if "%choice%"=="2" (
    echo Installing Anthropic package...
    pip install anthropic
    echo Done! Remember to set your Anthropic API Key in the app.
) else if "%choice%"=="3" (
    echo Skipping AI service installation. You can use offline mode.
) else (
    echo Invalid choice!
)

echo.
echo ====================================
echo   Installation Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Copy ai_config_example.json to ai_config.json
echo 2. Add your API keys to ai_config.json
echo 3. Run: python app_stock.py
echo.
pause
