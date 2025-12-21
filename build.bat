@echo off
chcp 65001 >nul
echo ========================================
echo   Сборка EtsyParser.exe
echo ========================================
echo.

REM Проверка наличия chromedriver
if not exist "drivers\chromedriver.exe" (
    echo ❌ ОШИБКА: drivers\chromedriver.exe не найден!
    echo.
    echo Скачайте ChromeDriver:
    echo https://googlechromelabs.github.io/chrome-for-testing/
    echo.
    echo Поместите chromedriver.exe в папку drivers\
    pause
    exit /b 1
)

echo ✅ ChromeDriver найден
echo.

REM Активация виртуального окружения
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Активация виртуального окружения...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ Виртуальное окружение не найдено, используем системный Python
)

echo.
echo 🔧 Обновление зависимостей...
pip install --upgrade pyinstaller selenium certifi >nul 2>&1

echo.
echo 🗑️ Очистка старой сборки...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo.
echo 🔨 Сборка exe файла...
pyinstaller EtsyParser_fixed.spec

echo.
if exist "dist\EtsyParser.exe" (
    echo ========================================
    echo   ✅ СБОРКА УСПЕШНА!
    echo ========================================
    echo.
    echo Файл: dist\EtsyParser.exe
    echo.
    
    REM Показываем размер файла
    for %%A in (dist\EtsyParser.exe) do echo Размер: %%~zA байт
    echo.
    
    echo Для запуска: dist\EtsyParser.exe
    echo.
) else (
    echo ========================================
    echo   ❌ ОШИБКА СБОРКИ!
    echo ========================================
    echo.
    echo Проверьте логи выше для деталей
    echo.
)

pause
