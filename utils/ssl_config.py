"""
Конфигурация SSL для работы requests в PyInstaller exe
"""
import os
from utils.driver_path import get_certifi_path


def configure_ssl():
    """
    Настраивает SSL сертификаты для requests
    Должна вызываться при старте приложения
    """
    cert_path = get_certifi_path()
    
    if os.path.exists(cert_path):
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        os.environ['SSL_CERT_FILE'] = cert_path
        return True
    return False
