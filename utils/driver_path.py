"""
Утилита для определения пути к ChromeDriver в exe и dev-режиме
"""
import sys
import os
from pathlib import Path


def get_chromedriver_path() -> str:
    """
    Возвращает путь к chromedriver.exe
    Работает как в exe (PyInstaller), так и в dev-режиме
    """
    # Проверяем, запущены ли мы из PyInstaller exe
    if getattr(sys, 'frozen', False):
        # Режим exe - используем sys._MEIPASS
        base_path = Path(sys._MEIPASS)
        driver_path = base_path / 'drivers' / 'chromedriver.exe'
    else:
        # Dev-режим - используем относительный путь от корня проекта
        base_path = Path(__file__).parent.parent
        driver_path = base_path / 'drivers' / 'chromedriver.exe'
    
    return str(driver_path)


def get_certifi_path() -> str:
    """
    Возвращает путь к certifi/cacert.pem
    Работает как в exe (PyInstaller), так и в dev-режиме
    """
    if getattr(sys, 'frozen', False):
        # Режим exe
        base_path = Path(sys._MEIPASS)
        cert_path = base_path / 'certifi' / 'cacert.pem'
    else:
        # Dev-режим - используем certifi из venv
        import certifi
        cert_path = Path(certifi.where())
    
    return str(cert_path)
