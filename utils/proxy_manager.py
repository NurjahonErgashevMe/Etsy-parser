"""
Менеджер для работы с резидентскими прокси
"""
import random
import logging
from typing import List, Dict, Optional, Tuple

class ProxyManager:
    """Менеджер для работы с прокси из файла proxies.txt"""
    
    def __init__(self, proxy_file_path: str = "proxies.txt"):
        self.proxy_file_path = proxy_file_path
        self.proxies = []
        self.current_proxy_index = 0
        self.load_proxies()
    
    def load_proxies(self) -> None:
        """Загружает прокси из файла"""
        try:
            with open(self.proxy_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            self.proxies = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    proxy_data = self.parse_proxy_line(line)
                    if proxy_data and self.validate_proxy_data(proxy_data):
                        self.proxies.append(proxy_data)
                    elif proxy_data:
                        logging.warning(f"⚠️ Невалидный прокси на строке {line_num}: {line}")
            
            logging.info(f"✅ Загружено {len(self.proxies)} прокси из {self.proxy_file_path}")
            
            if not self.proxies:
                logging.error("❌ Не найдено валидных прокси в файле!")
                
        except FileNotFoundError:
            logging.error(f"❌ Файл прокси не найден: {self.proxy_file_path}")
        except Exception as e:
            logging.error(f"❌ Ошибка при загрузке прокси: {e}")
    
    def parse_proxy_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Парсит строку прокси в формате: host:port:username:password
        Возвращает словарь с данными прокси
        """
        try:
            parts = line.split(':')
            if len(parts) >= 4:
                host = parts[0].strip()
                port = parts[1].strip()
                username = parts[2].strip()
                # Пароль может содержать символы ':', поэтому объединяем оставшиеся части
                password = ':'.join(parts[3:]).strip()
                
                return {
                    'host': host,
                    'port': port,
                    'username': username,
                    'password': password
                }
            else:
                logging.warning(f"⚠️ Неверный формат прокси: {line}")
                return None
        except Exception as e:
            logging.error(f"❌ Ошибка при парсинге прокси '{line}': {e}")
            return None
    
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Возвращает случайный прокси"""
        if not self.proxies:
            logging.error("❌ Нет доступных прокси!")
            return None
        
        proxy = random.choice(self.proxies)
        logging.info(f"🔄 Выбран случайный прокси: {proxy['host']}:{proxy['port']}")
        return proxy
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Возвращает следующий прокси по порядку"""
        if not self.proxies:
            logging.error("❌ Нет доступных прокси!")
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        
        logging.info(f"🔄 Выбран прокси #{self.current_proxy_index}: {proxy['host']}:{proxy['port']} (user: {proxy['username']})")
        return proxy
    
    def format_proxy_for_chrome(self, proxy_data: Dict[str, str]) -> str:
        """
        Форматирует прокси для использования в Chrome
        Возвращает строку вида: http://username:password@host:port
        """
        return f"http://{proxy_data['username']}:{proxy_data['password']}@{proxy_data['host']}:{proxy_data['port']}"
    
    def format_proxy_for_requests(self, proxy_data: Dict[str, str]) -> Dict[str, str]:
        """
        Форматирует прокси для использования в requests
        Возвращает словарь с http и https прокси
        """
        proxy_url = f"http://{proxy_data['username']}:{proxy_data['password']}@{proxy_data['host']}:{proxy_data['port']}"
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def get_proxy_auth_extension(self, proxy_data: Dict[str, str]) -> str:
        """
        Создает Chrome extension для аутентификации прокси
        Возвращает путь к папке расширения (не zip)
        """
        import os
        import tempfile
        import json
        import stat
        
        # Создаем временную папку для расширения с правильными правами
        try:
            extension_dir = tempfile.mkdtemp(prefix="proxy_auth_")
            # Устанавливаем полные права на папку
            os.chmod(extension_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        except Exception as e:
            logging.error(f"❌ Ошибка создания папки расширения: {e}")
            # Пробуем создать в текущей директории
            import uuid
            extension_dir = f"proxy_auth_{uuid.uuid4().hex[:8]}"
            os.makedirs(extension_dir, exist_ok=True)
            os.chmod(extension_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        
        # Экранируем специальные символы в пароле для JavaScript
        escaped_password = proxy_data['password'].replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        escaped_username = proxy_data['username'].replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        
        # Создаем manifest.json для Manifest V2 (более стабильный для прокси)
        manifest_content = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth Extension",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"],
                "persistent": True
            },
            "minimum_chrome_version": "22.0.0"
        }
        
        # Создаем background.js с улучшенной обработкой аутентификации
        background_content = f"""
// Данные прокси
const PROXY_HOST = "{proxy_data['host']}";
const PROXY_PORT = {proxy_data['port']};
const PROXY_USERNAME = "{escaped_username}";
const PROXY_PASSWORD = "{escaped_password}";

console.log("🚀 Proxy Auth Extension загружено");
console.log("📡 Прокси:", PROXY_HOST + ":" + PROXY_PORT);
console.log("👤 Пользователь:", PROXY_USERNAME);

// Настройка прокси
const proxyConfig = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: PROXY_HOST,
            port: PROXY_PORT
        }},
        bypassList: [
            "localhost",
            "127.0.0.1",
            "*.local",
            "10.*",
            "192.168.*",
            "172.16.*",
            "172.17.*",
            "172.18.*",
            "172.19.*",
            "172.20.*",
            "172.21.*",
            "172.22.*",
            "172.23.*",
            "172.24.*",
            "172.25.*",
            "172.26.*",
            "172.27.*",
            "172.28.*",
            "172.29.*",
            "172.30.*",
            "172.31.*"
        ]
    }}
}};

// Применяем настройки прокси
chrome.proxy.settings.set({{
    value: proxyConfig,
    scope: "regular"
}}, function() {{
    if (chrome.runtime.lastError) {{
        console.error("❌ Ошибка настройки прокси:", chrome.runtime.lastError);
    }} else {{
        console.log("✅ Настройки прокси применены успешно");
    }}
}});

// Основной обработчик аутентификации
function handleProxyAuth(details) {{
    console.log("🔐 Запрос аутентификации для:", details.url);
    console.log("🔐 Challenger:", details.challenger);
    
    // Проверяем, что это запрос к нашему прокси
    if (details.challenger && 
        (details.challenger.host === PROXY_HOST || 
         details.url.includes(PROXY_HOST))) {{
        
        console.log("✅ Предоставляем учетные данные для прокси");
        return {{
            authCredentials: {{
                username: PROXY_USERNAME,
                password: PROXY_PASSWORD
            }}
        }};
    }}
    
    console.log("⚠️ Запрос аутентификации не для нашего прокси, игнорируем");
    return {{}};
}}

// Регистрируем обработчик аутентификации
chrome.webRequest.onAuthRequired.addListener(
    handleProxyAuth,
    {{urls: ["<all_urls>"]}},
    ["blocking"]
);

// Дополнительный обработчик для отладки
chrome.webRequest.onBeforeRequest.addListener(
    function(details) {{
        if (details.url.includes("decodo.com") || details.url.includes("etsy.com")) {{
            console.log("📤 Запрос через прокси:", details.url);
        }}
    }},
    {{urls: ["<all_urls>"]}},
    []
);

// Обработчик ошибок прокси
chrome.webRequest.onErrorOccurred.addListener(
    function(details) {{
        if (details.error && details.error.toLowerCase().includes("proxy")) {{
            console.error("❌ Ошибка прокси:", details.error, "URL:", details.url);
        }}
    }},
    {{urls: ["<all_urls>"]}}
);

// Обработчик завершения запросов
chrome.webRequest.onCompleted.addListener(
    function(details) {{
        if (details.url.includes("decodo.com") || details.url.includes("etsy.com")) {{
            console.log("✅ Запрос завершен:", details.statusCode, details.url);
        }}
    }},
    {{urls: ["<all_urls>"]}}
);

console.log("🎯 Расширение готово к работе!");
"""
        
        # Записываем файлы с правильными правами
        try:
            manifest_path = os.path.join(extension_dir, "manifest.json")
            with open(manifest_path, "w", encoding='utf-8') as f:
                json.dump(manifest_content, f, indent=2, ensure_ascii=False)
            os.chmod(manifest_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            
            background_path = os.path.join(extension_dir, "background.js")
            with open(background_path, "w", encoding='utf-8') as f:
                f.write(background_content)
            os.chmod(background_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            
            logging.info(f"✅ Создано расширение для прокси: {extension_dir}")
            logging.info(f"📁 Путь к расширению: {extension_dir}")
            
            return extension_dir
            
        except Exception as e:
            logging.error(f"❌ Ошибка записи файлов расширения: {e}")
            # Очищаем папку при ошибке
            try:
                import shutil
                shutil.rmtree(extension_dir, ignore_errors=True)
            except:
                pass
            raise e
    
    def get_chrome_args_with_proxy(self, proxy_data: Dict[str, str]) -> List[str]:
        """
        Возвращает аргументы командной строки для Chrome с прокси
        Это более надежный способ, чем расширения
        """
        proxy_server = f"{proxy_data['host']}:{proxy_data['port']}"
        
        chrome_args = [
            f"--proxy-server=http://{proxy_server}",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions-except=",
            "--disable-plugins-discovery",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-popup-blocking",
            "--disable-translate",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-device-discovery-notifications",
            "--disable-background-networking",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-report-upload",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--remote-debugging-port=9222"
        ]
        
        logging.info(f"🔧 Chrome аргументы для прокси {proxy_server} подготовлены")
        return chrome_args
    
    def create_proxy_auth_script(self, proxy_data: Dict[str, str]) -> str:
        """
        Создает JavaScript скрипт для автоматической аутентификации в прокси
        """
        script_content = f"""
// Автоматическая аутентификация прокси
(function() {{
    const username = "{proxy_data['username']}";
    const password = "{proxy_data['password']}";
    
    // Перехватываем диалоги аутентификации
    const originalAlert = window.alert;
    const originalConfirm = window.confirm;
    const originalPrompt = window.prompt;
    
    // Автоматически заполняем поля аутентификации
    function autoFillAuth() {{
        const usernameField = document.querySelector('input[type="text"], input[name*="user"], input[id*="user"]');
        const passwordField = document.querySelector('input[type="password"], input[name*="pass"], input[id*="pass"]');
        
        if (usernameField && passwordField) {{
            usernameField.value = username;
            passwordField.value = password;
            
            // Ищем кнопку входа
            const loginButton = document.querySelector('button[type="submit"], input[type="submit"], button:contains("Войти"), button:contains("Login")');
            if (loginButton) {{
                loginButton.click();
            }}
        }}
    }}
    
    // Запускаем автозаполнение при загрузке страницы
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', autoFillAuth);
    }} else {{
        autoFillAuth();
    }}
    
    // Также пробуем через небольшую задержку
    setTimeout(autoFillAuth, 1000);
    setTimeout(autoFillAuth, 3000);
}})();
"""
        
        import tempfile
        import os
        
        script_path = os.path.join(tempfile.gettempdir(), "proxy_auth_script.js")
        with open(script_path, "w", encoding='utf-8') as f:
            f.write(script_content)
        
        logging.info(f"📝 Создан скрипт автоаутентификации: {script_path}")
        return script_path
    
    def test_proxy(self, proxy_data: Dict[str, str]) -> bool:
        """
        Тестирует прокси с помощью простого HTTP запроса
        """
        try:
            import requests
            
            proxy_dict = self.format_proxy_for_requests(proxy_data)
            
            # Тестируем прокси
            response = requests.get(
                'https://ip.decodo.com/json',
                proxies=proxy_dict,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"✅ Прокси работает. IP: {result.get('ip', 'unknown')}")
                return True
            else:
                logging.error(f"❌ Прокси не работает. Статус: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Ошибка при тестировании прокси: {e}")
            return False
    
    def get_working_proxy(self) -> Optional[Dict[str, str]]:
        """
        Возвращает первый рабочий прокси из списка
        """
        if not self.proxies:
            return None
        
        # Перемешиваем прокси для случайного выбора
        shuffled_proxies = self.proxies.copy()
        random.shuffle(shuffled_proxies)
        
        for proxy in shuffled_proxies[:5]:  # Тестируем максимум 5 прокси
            logging.info(f"🧪 Тестируем прокси: {proxy['host']}:{proxy['port']}")
            if self.test_proxy(proxy):
                return proxy
        
        logging.error("❌ Не найдено рабочих прокси!")
        return None
    
    def validate_proxy_data(self, proxy_data: Dict[str, str]) -> bool:
        """Проверяет валидность данных прокси"""
        required_fields = ['host', 'port', 'username', 'password']
        
        for field in required_fields:
            if field not in proxy_data or not proxy_data[field]:
                logging.error(f"❌ Отсутствует поле '{field}' в данных прокси")
                return False
        
        # Проверяем, что порт - число
        try:
            port = int(proxy_data['port'])
            if not (1 <= port <= 65535):
                logging.error(f"❌ Неверный порт: {proxy_data['port']}")
                return False
        except ValueError:
            logging.error(f"❌ Порт должен быть числом: {proxy_data['port']}")
            return False
        
        return True
    
    def cleanup_proxy_extension(self, extension_path: str) -> None:
        """Очищает временные файлы расширения прокси"""
        try:
            import os
            import shutil
            if os.path.exists(extension_path):
                # Сначала пытаемся изменить права доступа для удаления
                try:
                    import stat
                    for root, dirs, files in os.walk(extension_path):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                        for f in files:
                            os.chmod(os.path.join(root, f), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                except:
                    pass  # Игнорируем ошибки chmod
                
                shutil.rmtree(extension_path, ignore_errors=True)
                logging.info(f"🧹 Временное расширение прокси удалено: {extension_path}")
        except Exception as e:
            logging.warning(f"⚠️ Ошибка при удалении расширения прокси: {e}")
    
    def get_proxy_stats(self) -> Dict[str, int]:
        """Возвращает статистику по прокси"""
        return {
            'total_proxies': len(self.proxies),
            'current_index': self.current_proxy_index
        }