# -*- coding: utf-8 -*-
"""Упрощенная сборка .exe для EtsyParser"""
import os
import sys
import subprocess

def build():
    print("Начинаем сборку EtsyParser.exe...")
    
    # Получаем путь к certifi
    try:
        import certifi
        certifi_path = os.path.dirname(certifi.where())
        print(f"Certifi path: {certifi_path}")
    except ImportError:
        print("ОШИБКА: certifi не найден!")
        return False
    
    # Команда PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=EtsyParser",
        "--onefile",
        "--clean",
        "--windowed",  # Без консоли
        f"--add-data=config-main.txt{os.pathsep}.",
        f"--add-data=logs{os.pathsep}logs",
        f"--add-data=output{os.pathsep}output",
        f"--add-data=gui{os.pathsep}gui",
        f"--add-data=core{os.pathsep}core",
        f"--add-data=config{os.pathsep}config",
        f"--add-data=utils{os.pathsep}utils",
        f"--add-data=parsers{os.pathsep}parsers",
        f"--add-data=services{os.pathsep}services",
        f"--add-data=models{os.pathsep}models",
        f"--add-data=bot{os.pathsep}bot",
        f"--add-data=drivers{os.pathsep}drivers",  # ChromeDriver
        f"--add-data={certifi_path}{os.pathsep}certifi",  # SSL certs
        "--hidden-import=tkinter",
        "--hidden-import=selenium",
        "--hidden-import=certifi",
        "--hidden-import=aiogram",
        "--hidden-import=requests",
        "main.py"
    ]
    
    # Добавляем credentials если есть
    if os.path.exists("credentials.json"):
        cmd.insert(-1, f"--add-data=credentials.json{os.pathsep}.")
    
    print("Запускаем PyInstaller...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode == 0:
        print("\n[OK] Сборка завершена успешно!")
        exe_path = os.path.join("dist", "EtsyParser.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"Размер файла: {size_mb:.1f} MB")
            print(f"Путь: {os.path.abspath(exe_path)}")
            return True
        else:
            print("[ERROR] .exe файл не найден после сборки!")
            return False
    else:
        print("\n[ERROR] Ошибка сборки!")
        print("STDOUT:", result.stdout[-1000:] if result.stdout else "")
        print("STDERR:", result.stderr[-1000:] if result.stderr else "")
        return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
