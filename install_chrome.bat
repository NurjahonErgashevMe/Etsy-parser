@echo off
echo ========================================
echo    УСТАНОВКА GOOGLE CHROME ДЛЯ VDS
echo ========================================
echo.

echo 🔍 Проверяем наличие Chrome...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo ✅ Chrome уже установлен!
    echo 📍 Путь: C:\Program Files\Google\Chrome\Application\chrome.exe
    goto :end
)

if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo ✅ Chrome уже установлен!
    echo 📍 Путь: C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
    goto :end
)

echo 📥 Chrome не найден. Начинаем загрузку...
echo.

echo 🌐 Скачиваем Chrome установщик...
powershell -Command "Invoke-WebRequest -Uri 'https://dl.google.com/chrome/install/latest/chrome_installer.exe' -OutFile 'chrome_installer.exe'"

if not exist "chrome_installer.exe" (
    echo ❌ Ошибка загрузки Chrome!
    echo 💡 Попробуйте скачать вручную: https://www.google.com/chrome/
    pause
    exit /b 1
)

echo ✅ Chrome установщик загружен!
echo.

echo 🚀 Запускаем установку Chrome...
echo ⏳ Подождите, установка может занять несколько минут...
chrome_installer.exe /silent /install

echo.
echo ⏳ Ожидаем завершения установки...
timeout /t 30 /nobreak >nul

echo.
echo 🔍 Проверяем установку...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo ✅ Chrome успешно установлен!
    echo 📍 Путь: C:\Program Files\Google\Chrome\Application\chrome.exe
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo ✅ Chrome успешно установлен!
    echo 📍 Путь: C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
) else (
    echo ❌ Chrome не найден после установки!
    echo 💡 Возможно, нужно больше времени или ручная установка
)

echo.
echo 🧹 Удаляем установочный файл...
if exist "chrome_installer.exe" del "chrome_installer.exe"

:end
echo.
echo ========================================
echo           УСТАНОВКА ЗАВЕРШЕНА
echo ========================================
echo.
echo 🎉 Теперь можно запускать Etsy Parser!
echo.
pause