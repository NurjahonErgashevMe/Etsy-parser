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
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxy_data = self.parse_proxy_line(line)
                    if proxy_data:
                        self.proxies.append(proxy_data)
            
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
            if len(parts) == 4:
                host, port, username, password = parts
                return {
                    'host': host.strip(),
                    'port': port.strip(),
                    'username': username.strip(),
                    'password': password.strip()
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
        
        logging.info(f"🔄 Выбран прокси #{self.current_proxy_index}: {proxy['host']}:{proxy['port']}")
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
        Возвращает путь к созданному расширению
        """
        import os
        import zipfile
        import tempfile
        
        # Создаем временную папку для расширения
        extension_dir = tempfile.mkdtemp(prefix="proxy_auth_")
        
        # Создаем manifest.json
        manifest_content = """{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy Auth",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking",
        "activeTab"
    ],
    "background": {
        "scripts": ["background.js"],
        "persistent": true
    },
    "minimum_chrome_version":"22.0.0"
}"""
        
        # Создаем background.js
        background_content = f"""
console.log("Proxy extension starting...");

// Настройка прокси
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{proxy_data['host']}",
            port: parseInt({proxy_data['port']})
        }},
        bypassList: ["localhost", "127.0.0.1", "*.local"]
    }}
}};

// Устанавливаем настройки прокси
chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
    if (chrome.runtime.lastError) {{
        console.error("Proxy settings error:", chrome.runtime.lastError);
    }} else {{
        console.log("Proxy settings applied successfully");
    }}
}});

// Обработчик аутентификации - более агрессивный подход
function handleAuth(details) {{
    console.log("Proxy authentication requested for:", details.url);
    console.log("Providing credentials for proxy: {proxy_data['host']}:{proxy_data['port']}");
    
    return {{
        authCredentials: {{
            username: "{proxy_data['username']}",
            password: "{proxy_data['password']}"
        }}
    }};
}}

// Добавляем слушатель для аутентификации с максимальными правами
chrome.webRequest.onAuthRequired.addListener(
    handleAuth,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);

// Дополнительный обработчик для перехвата всех запросов аутентификации
chrome.webRequest.onBeforeRequest.addListener(
    function(details) {{
        console.log("Request to:", details.url);
    }},
    {{urls: ["<all_urls>"]}},
    []
);

// Обработчик ошибок
chrome.webRequest.onErrorOccurred.addListener(
    function(details) {{
        if (details.error.includes("PROXY")) {{
            console.error("Proxy error:", details.error, "for URL:", details.url);
        }}
    }},
    {{urls: ["<all_urls>"]}}
);

console.log("Proxy extension loaded with: {proxy_data['host']}:{proxy_data['port']}");
console.log("Username: {proxy_data['username']}");
"""
        
        # Записываем файлы
        with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
            f.write(manifest_content)
        
        with open(os.path.join(extension_dir, "background.js"), "w") as f:
            f.write(background_content)
        
        # Создаем zip архив расширения
        extension_path = os.path.join(tempfile.gettempdir(), f"proxy_auth_{proxy_data['host']}_{proxy_data['port']}.zip")
        
        with zipfile.ZipFile(extension_path, 'w') as zip_file:
            zip_file.write(os.path.join(extension_dir, "manifest.json"), "manifest.json")
            zip_file.write(os.path.join(extension_dir, "background.js"), "background.js")
        
        logging.info(f"✅ Создано расширение для прокси: {extension_path}")
        return extension_path
    
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