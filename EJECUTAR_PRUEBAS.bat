@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=py"
    ) else (
        set "PYTHON=python"
    )
)

echo.
echo ============================================================
echo   PLAN DE PRUEBAS SIMEL EL TAMBO - PMV 1 + PMV 2
echo ============================================================
echo.

"%PYTHON%" "%~dp0ejecutar_pruebas.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo RESULTADO GENERAL: PASS
) else (
    echo RESULTADO GENERAL: FAIL
)
echo.
pause
exit /b %EXIT_CODE%
