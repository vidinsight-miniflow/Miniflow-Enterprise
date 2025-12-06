@echo off
REM MiniFlow Enterprise - Başlatma Scripti (Windows)
REM Kullanım: start.bat [setup|run|help]

REM Proje root dizinine git
cd /d %~dp0

REM PYTHONPATH ayarla
set PYTHONPATH=%PYTHONPATH%;%CD%\src

REM Komut al (varsayılan: run)
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=run

REM Eğer run komutu verilmişse veya hiçbir şey verilmemişse
if "%COMMAND%"=="run" (
    echo 🔍 Setup kontrolü yapılıyor...
    echo.
    
    REM Önce setup yap
    python -m src.miniflow setup
    
    REM Setup başarılı mı kontrol et
    if errorlevel 1 (
        echo.
        echo ❌ Setup başarısız oldu! Run komutu çalıştırılamadı.
        echo    Lütfen setup hatalarını düzeltin ve tekrar deneyin.
        exit /b %errorlevel%
    )
    
    echo.
    echo ✅ Setup başarılı! Uygulama başlatılıyor...
    echo.
    
    REM Setup başarılıysa run yap
    python -m src.miniflow run
) else (
    REM Diğer komutlar (setup, help, vb.) direkt çalıştır
    python -m src.miniflow %*
)

