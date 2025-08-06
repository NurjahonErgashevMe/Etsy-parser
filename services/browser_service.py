"""
Сервис для работы с браузером через Selenium Stealth с поддержкой резидентских прокси
"""
import time
import json
import os
import tempfile
import logging
from typing import Dict, Optional, List
try:
    from seleniumwire import webdriver
    SELENIUM_WIRE_AVAILABLE = True
except ImportError:
    from selenium import webdriver
    SELENIUM_WIRE_AVAILABLE = False
    
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from utils.proxy_manager import ProxyManager

class BrowserService:
    """Сервис для работы с браузером"""
    
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.captured_headers = {}
        self.max_retries = 3
        self.wait_timeout = 90  # 1.5 минуты
        self.proxy_manager = ProxyManager()
        self.current_proxy = None
        self.proxy_extension_path = None
    
    def _check_chrome_installation(self) -> bool:
        """Проверяет наличие установленного Chrome"""
        import os
        import subprocess
        
        logging.info("🔍 Проверяем установку Google Chrome...")
        
        # Возможные пути к Chrome на Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        # Проверяем наличие файла Chrome
        for path in chrome_paths:
            if os.path.exists(path):
                logging.info(f"✅ Chrome найден: {path}")
                return True
        
        # Пытаемся запустить chrome через командную строку
        try:
            result = subprocess.run(["chrome", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logging.info(f"✅ Chrome найден в PATH: {result.stdout.strip()}")
                return True
        except:
            pass
        
        logging.error("❌ Google Chrome не найден!")
        logging.error("💡 Установите Google Chrome: https://www.google.com/chrome/")
        logging.error("💡 Или убедитесь, что Chrome установлен в стандартной папке")
        return False
        
    def setup_driver(self, use_proxy: bool = True):
        """Настройка Chrome драйвера с stealth режимом, имитацией человека и прокси"""
        # Проверяем наличие Chrome
        if not self._check_chrome_installation():
            return False
        
        # Получаем случайный рабочий прокси если нужно
        if use_proxy:
            self.current_proxy = self.proxy_manager.get_random_proxy()
            if not self.current_proxy:
                logging.error("❌ Не удалось получить прокси!")
                return False
            logging.info(f"🌐 Используем случайный прокси: {self.current_proxy['host']}:{self.current_proxy['port']}")
        else:
            logging.info("🌐 Запуск без прокси")
            
        chrome_options = Options()
        
        # Основные опции для stealth режима
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Открываем браузер в полноэкранном режиме
        chrome_options.add_argument("--start-maximized")
        
        # Настройки для скорости - загружаем только HTML и CSS
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Отключаем изображения
            "profile.default_content_setting_values.notifications": 2,  # Отключаем уведомления
            "profile.default_content_settings.popups": 0,  # Отключаем попапы
            "profile.managed_default_content_settings.media_stream": 2,  # Отключаем медиа
            "profile.managed_default_content_settings.stylesheets": 1,  # Оставляем CSS
            "profile.managed_default_content_settings.javascript": 1,   # ВКЛЮЧАЕМ JS (сайт требует)
            "profile.managed_default_content_settings.plugins": 2,  # Отключаем плагины
            "profile.managed_default_content_settings.geolocation": 2,  # Отключаем геолокацию
            "profile.managed_default_content_settings.media_stream_mic": 2,  # Отключаем микрофон
            "profile.managed_default_content_settings.media_stream_camera": 2,  # Отключаем камеру
            "profile.default_content_setting_values.automatic_downloads": 2,  # Отключаем автозагрузки
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Дополнительные опции для ускорения
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--aggressive-cache-discard")
        chrome_options.add_argument("--memory-pressure-off")
        
        # Включаем логирование сетевых запросов, но подавляем ошибки GPU
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=3")  # Только фатальные ошибки
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-gpu-logging")
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # Дополнительные опции для блокировки ненужных ресурсов
        chrome_options.add_argument("--disable-extensions-except")
        chrome_options.add_argument("--disable-plugins-discovery")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-translate")
        chrome_options.add_argument("--disable-web-resources")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-component-extensions-with-background-pages")
        chrome_options.add_argument("--disable-background-downloads")
        chrome_options.add_argument("--disable-add-to-shelf")
        chrome_options.add_argument("--disable-datasaver-prompt")
        chrome_options.add_argument("--disable-domain-reliability")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor,TranslateUI")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Дополнительная блокировка изображений
        
        # Дополнительные опции для стабильности
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-gpu-sandbox")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        
        # Настройка прокси
        seleniumwire_options = None
        if use_proxy and self.current_proxy:
            if SELENIUM_WIRE_AVAILABLE:
                seleniumwire_options = self._get_seleniumwire_proxy_options()
            else:
                self._setup_proxy_options(chrome_options)
        
        try:
            logging.info("🔧 Устанавливаем ChromeDriver...")
            
            # Пытаемся установить ChromeDriver с обработкой ошибок
            try:
                driver_path = ChromeDriverManager().install()
                logging.info(f"✅ ChromeDriver путь: {driver_path}")
                
                # Проверяем, что путь указывает на правильный файл
                if not driver_path.endswith('chromedriver.exe'):
                    # Ищем chromedriver.exe в той же папке
                    driver_dir = os.path.dirname(driver_path)
                    chromedriver_exe = os.path.join(driver_dir, 'chromedriver.exe')
                    if os.path.exists(chromedriver_exe):
                        driver_path = chromedriver_exe
                        logging.info(f"🔧 Исправлен путь к ChromeDriver: {driver_path}")
                    else:
                        logging.error(f"❌ chromedriver.exe не найден в {driver_dir}")
                        raise Exception("ChromeDriver executable not found")
                
                service = Service(driver_path)
            except Exception as e:
                logging.error(f"❌ Ошибка установки ChromeDriver: {e}")
                logging.info("🔄 Пытаемся использовать системный ChromeDriver...")
                service = Service()  # Попробуем системный драйвер
            
            logging.info("🚀 Запускаем Chrome браузер...")
            if seleniumwire_options:
                self.driver = webdriver.Chrome(
                    service=service, 
                    options=chrome_options,
                    seleniumwire_options=seleniumwire_options
                )
                # Настраиваем блокировку ненужных ресурсов
                self._setup_request_blocking()
            else:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Применяем stealth настройки
            stealth(self.driver,
                   languages=["ru-RU", "ru"],
                   vendor="Google Inc.",
                   platform="Win32",
                   webgl_vendor="Intel Inc.",
                   renderer="Intel Iris OpenGL Engine",
                   fix_hairline=True)
            
            # Максимизируем окно браузера
            self.driver.maximize_window()
            
            # Добавляем имитацию человеческого поведения
            self._setup_human_behavior()
            
            # Проверяем IP если используем прокси
            if use_proxy and self.current_proxy:
                self._verify_proxy_ip()
            
            logging.info("✅ Браузер успешно запущен в stealth режиме с имитацией человека")
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка при запуске браузера: {e}")
            logging.error(f"❌ Тип ошибки: {type(e).__name__}")
            logging.error(f"❌ Подробности ошибки: {str(e)}")
            
            # Очищаем временные файлы прокси при ошибке
            self._cleanup_proxy_extension()
            
            # Пытаемся диагностировать проблему
            if "WinError 193" in str(e):
                logging.error("🔍 Диагностика: Проблема с исполняемым файлом Chrome")
                logging.error("💡 Возможные решения:")
                logging.error("   1. Установите Google Chrome: https://www.google.com/chrome/")
                logging.error("   2. Перезапустите терминал/IDE")
                logging.error("   3. Проверьте PATH переменную")
            elif "chromedriver" in str(e).lower():
                logging.error("🔍 Диагностика: Проблема с ChromeDriver")
                logging.error("💡 Попробуйте переустановить ChromeDriver")
            elif "proxy" in str(e).lower():
                logging.error("🔍 Диагностика: Проблема с прокси")
                logging.error("💡 Проверьте настройки прокси в proxies.txt")
            elif "timeout" in str(e).lower():
                logging.error("🔍 Диагностика: Таймаут при запуске браузера")
                logging.error("💡 Возможно, прокси не отвечает или заблокирован")
            elif "connection" in str(e).lower():
                logging.error("🔍 Диагностика: Проблема с подключением")
                logging.error("💡 Проверьте интернет-соединение и прокси")
            
            return False
    
    def _setup_human_behavior(self):
        """Настройка имитации человеческого поведения"""
        try:
            # Убираем флаг webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Добавляем реалистичные свойства navigator
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            # Имитируем движение мыши
            self.driver.execute_script("""
                document.addEventListener('mousemove', function(e) {
                    window.mouseX = e.clientX;
                    window.mouseY = e.clientY;
                });
            """)
            
            logging.info("🤖 Настроена имитация человеческого поведения")
            
        except Exception as e:
            logging.error(f"⚠️ Ошибка при настройке имитации человека: {e}")
    
    def _get_seleniumwire_proxy_options(self):
        """Возвращает настройки прокси для selenium-wire"""
        proxy_url = self.proxy_manager.format_proxy_for_chrome(self.current_proxy)
        
        return {
            'proxy': {
                'http': proxy_url,
                'https': proxy_url,
            }
        }
    
    def _setup_proxy_options(self, chrome_options: Options):
        """Настраивает опции Chrome для работы с прокси"""
        try:
            # Пробуем создать расширение для аутентификации прокси
            try:
                self.proxy_extension_path = self.proxy_manager.get_proxy_auth_extension(self.current_proxy)
                # Добавляем расширение в Chrome (должно быть до других опций)
                chrome_options.add_extension(self.proxy_extension_path)
                logging.info("✅ Расширение прокси создано и добавлено")
            except Exception as ext_error:
                logging.warning(f"⚠️ Не удалось создать расширение прокси: {ext_error}")
                logging.info("🔄 Используем альтернативный метод настройки прокси")
                
                # Альтернативный способ - только через аргументы командной строки
                # В этом случае может потребоваться ручная аутентификация
                pass
            
            # Настройка прокси через аргументы командной строки
            proxy_server = f"{self.current_proxy['host']}:{self.current_proxy['port']}"
            chrome_options.add_argument(f"--proxy-server=http://{proxy_server}")
            
            # Отключаем различные проверки безопасности для прокси
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors-spki-list")
            chrome_options.add_argument("--ignore-certificate-errors-ssl-errors")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-cross-origin-auth-prompt")
            
            # Отключаем диалоги аутентификации
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            logging.info(f"🔧 Настроен прокси: {self.current_proxy['host']}:{self.current_proxy['port']}")
            
        except Exception as e:
            logging.error(f"❌ Ошибка при настройке прокси: {e}")
            raise e
    
    def _verify_proxy_ip(self):
        """Проверяет текущий IP адрес через прокси"""
        try:
            logging.info("🔍 Проверяем IP адрес через прокси...")
            
            # Переходим на сайт для проверки IP
            self.driver.get("https://ip.decodo.com/json")
            time.sleep(3)
            
            # Получаем результат
            page_source = self.driver.page_source
            if "ip" in page_source.lower():
                logging.info(f"✅ IP проверен через прокси")
                # Можно извлечь IP из JSON если нужно
                import re
                ip_match = re.search(r'"ip":\s*"([^"]+)"', page_source)
                if ip_match:
                    current_ip = ip_match.group(1)
                    logging.info(f"🌐 Текущий IP: {current_ip}")
            else:
                logging.warning("⚠️ Не удалось получить информацию об IP")
                
        except Exception as e:
            logging.error(f"⚠️ Ошибка при проверке IP: {e}")
    
    def _handle_captcha(self, max_wait_time: int = 60) -> bool:
        """
        Обрабатывает капчу, ожидая её решения пользователем или автоматически
        """
        try:
            current_url = self.driver.current_url.lower()
            
            if 'captcha-delivery.com' not in current_url:
                return True  # Капчи нет
            
            logging.info("🤖 ОБНАРУЖЕНА КАПЧА! Ожидаем решения...")
            logging.info(f"🔗 URL капчи: {self.driver.current_url}")
            
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    current_url = self.driver.current_url.lower()
                    
                    # Проверяем, ушли ли мы с капчи
                    if 'captcha-delivery.com' not in current_url:
                        logging.info("✅ Капча решена! Продолжаем работу...")
                        return True
                    
                    # Проверяем, не появилась ли кнопка продолжения
                    try:
                        continue_buttons = self.driver.find_elements(By.XPATH, 
                            "//button[contains(text(), 'Continue') or contains(text(), 'Продолжить')]")
                        if continue_buttons:
                            logging.info("🔘 Найдена кнопка продолжения, нажимаем...")
                            continue_buttons[0].click()
                            time.sleep(3)
                            continue
                    except:
                        pass
                    
                    # Ждем немного перед следующей проверкой
                    time.sleep(2)
                    
                except Exception as e:
                    logging.error(f"⚠️ Ошибка при обработке капчи: {e}")
                    time.sleep(2)
            
            logging.error(f"❌ Капча не была решена за {max_wait_time} секунд")
            return False
            
        except Exception as e:
            logging.error(f"❌ Ошибка при обработке капчи: {e}")
            return False
    
    def _cleanup_proxy_extension(self):
        """Очищает временные файлы расширения прокси"""
        try:
            if self.proxy_extension_path and os.path.exists(self.proxy_extension_path):
                # Используем метод из ProxyManager для правильной очистки
                self.proxy_manager.cleanup_proxy_extension(self.proxy_extension_path)
                self.proxy_extension_path = None
        except Exception as e:
            logging.error(f"⚠️ Ошибка при удалении расширения прокси: {e}")
    
    def change_proxy(self) -> bool:
        """Меняет прокси на новый и перезапускает браузер"""
        logging.info("🔄 Смена прокси...")
        
        # Закрываем текущий браузер
        self.close_browser()
        
        # Получаем новый прокси
        self.current_proxy = self.proxy_manager.get_random_proxy()
        if not self.current_proxy:
            logging.error("❌ Не удалось получить новый прокси!")
            return False
        
        logging.info(f"🌐 Новый прокси: {self.current_proxy['host']}:{self.current_proxy['port']}")
        
        # Запускаем браузер с новым прокси
        return self.setup_driver(use_proxy=True)
    
    def simulate_human_actions(self):
        """Имитирует человеческие действия на странице"""
        try:
            import random
            
            print("🤖 Имитируем человеческое поведение...")
            
            # Случайная пауза перед началом
            time.sleep(random.uniform(2, 4))
            
            # Имитируем чтение страницы - медленный скролл вниз
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            scroll_steps = random.randint(3, 6)
            
            for step in range(scroll_steps):
                # Случайный размер скролла
                scroll_amount = random.randint(200, 600)
                current_position += scroll_amount
                
                # Плавный скролл
                self.driver.execute_script(f"""
                    window.scrollTo({{
                        top: {current_position},
                        behavior: 'smooth'
                    }});
                """)
                
                # Пауза как будто читаем контент
                time.sleep(random.uniform(1, 2.5))
                
                # Иногда скроллим немного назад (как человек)
                if random.random() < 0.3:
                    back_scroll = random.randint(50, 150)
                    self.driver.execute_script(f"""
                        window.scrollTo({{
                            top: {current_position - back_scroll},
                            behavior: 'smooth'
                        }});
                    """)
                    time.sleep(random.uniform(0.5, 1))
            
            # Имитируем движение мыши в разных частях страницы
            self._simulate_realistic_mouse_movement()
            
            # Возвращаемся к началу страницы
            self.driver.execute_script("""
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            """)
            time.sleep(random.uniform(1, 2))
            
            print("✅ Имитация человеческого поведения завершена")
            
        except Exception as e:
            print(f"⚠️ Ошибка при имитации действий: {e}")
    
    def _simulate_realistic_mouse_movement(self):
        """Имитирует реалистичные движения мыши"""
        try:
            import random
            
            # Получаем размеры окна
            window_size = self.driver.get_window_size()
            width = window_size['width']
            height = window_size['height']
            
            # Делаем несколько случайных движений мыши
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, width - 100)
                y = random.randint(100, height - 100)
                
                # Имитируем движение мыши
                self.driver.execute_script(f"""
                    var event = new MouseEvent('mousemove', {{
                        clientX: {x},
                        clientY: {y},
                        bubbles: true
                    }});
                    document.dispatchEvent(event);
                """)
                
                time.sleep(random.uniform(0.3, 0.8))
                
        except Exception as e:
            print(f"⚠️ Ошибка при имитации движения мыши: {e}")
    
    def wait_for_successful_request(self, target_url: str):
        """Ждет успешного запроса (200) к целевому URL. Возвращает (success, status_code)"""
        print(f"🔍 Ожидание успешного запроса к: {target_url}")
        
        start_time = time.time()
        last_status = None
        last_activity_time = start_time
        inactivity_timeout = 60  # 1 минута бездействия
        
        while time.time() - start_time < self.wait_timeout:
            try:
                # Получаем логи производительности
                logs = self.driver.get_log('performance')
                
                # Если есть новые логи, обновляем время последней активности
                if logs:
                    last_activity_time = time.time()
                
                for log in logs:
                    message = json.loads(log['message'])
                    
                    # Ищем сетевые запросы
                    if message['message']['method'] == 'Network.responseReceived':
                        response = message['message']['params']['response']
                        url = response['url']
                        status = response['status']
                        
                        # Проверяем, это ли наш целевой URL
                        if target_url in url:
                            last_status = status
                            
                            if status == 200:
                                print(f"✅ Получен успешный ответ (200) для {url}")
                                
                                # Захватываем headers
                                self.captured_headers = response.get('headers', {})
                                print(f"📋 Захвачено {len(self.captured_headers)} headers")
                                
                                return True, 200
                            elif status == 403:
                                print(f"🚫 Получен 403 ответ для {url}")
                                return False, 403
                            elif status == 429:
                                print(f"⚠️ Получен 429 (Too Many Requests) для {url}")
                                return False, 429
                            else:
                                print(f"⚠️ Получен {status} ответ для {url}")
                
                # Проверяем бездействие страницы
                current_time = time.time()
                if current_time - last_activity_time > inactivity_timeout:
                    print(f"⏰ Страница бездействует {inactivity_timeout}s - принудительная перезагрузка")
                    self.driver.refresh()
                    self._wait_for_page_load()
                    last_activity_time = current_time
                    print("🔄 Страница перезагружена, продолжаем ожидание...")
                
                time.sleep(1)  # Небольшая пауза между проверками
                
            except Exception as e:
                print(f"Ошибка при проверке логов: {e}")
                time.sleep(1)
        
        print(f"⏰ Таймаут ожидания ({self.wait_timeout}s) для {target_url}")
        return False, last_status or 'timeout'
    

    
    def load_page_with_403_handling(self, url: str) -> tuple[bool, bool]:
        """
        Загружает страницу с обработкой 403 ошибок.
        При получении 403 делает 3 попытки перезагрузки (может быть капча),
        только после 3 неудач требует перезапуск браузера.
        Возвращает (success, need_browser_restart)
        """
        shop_name = url.split('/')[-1] if '/' in url else 'unknown'
        max_403_retries = 3
        
        for attempt in range(max_403_retries):
            print(f"\n🚀 Попытка {attempt + 1}/{max_403_retries} загрузки {shop_name}")
            
            try:
                # Загружаем страницу
                self.driver.get(url)
                
                # Ждем появления основных элементов
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    logging.info("📄 Страница загружена, ожидаем успешного запроса...")
                except TimeoutException:
                    logging.info("⚠️ Страница загружается медленно...")
                
                # Проверяем на капчу и обрабатываем её
                if 'captcha-delivery.com' in self.driver.current_url.lower():
                    logging.info("🤖 Обнаружена капча, пытаемся обработать...")
                    if not self._handle_captcha(max_wait_time=30):
                        logging.info("❌ Не удалось обработать капчу, требуется смена прокси")
                        return False, True
                
                # Имитируем человеческие действия после загрузки
                self.simulate_human_actions()
                
                # Ждем успешного запроса и получаем статус
                success, status = self.wait_for_successful_request(url)
                
                if success:
                    logging.info(f"✅ Страница {shop_name} успешно загружена!")
                    return True, False
                elif status == 403:
                    logging.info(f"🚫 Получен 403 для {shop_name} (попытка {attempt + 1}/{max_403_retries})")
                    
                    if attempt < max_403_retries - 1:
                        logging.info("🔄 Перезагружаем страницу через 10 секунд (возможно капча)...")
                        time.sleep(10)
                        self.driver.refresh()
                        self._wait_for_page_load()
                        continue
                    else:
                        logging.info("❌ Получен 403 после 3 попыток - требуется новый браузер")
                        return False, True
                else:
                    # Другие ошибки
                    logging.info(f"❌ Получен статус {status} для {shop_name}")
                    return False, False
                    
            except WebDriverException as e:
                logging.error(f"❌ Ошибка WebDriver: {e}")
                if attempt < max_403_retries - 1:
                    time.sleep(5)
                else:
                    return False, True
        
        return False, False

    def load_page_with_retries(self, url: str) -> bool:
        """Загружает страницу с повторными попытками при различных ошибках"""
        shop_name = url.split('/')[-1] if '/' in url else 'unknown'
        
        for attempt in range(self.max_retries):
            print(f"\n🚀 Попытка {attempt + 1}/{self.max_retries} загрузки {shop_name}")
            
            try:
                # Загружаем страницу
                self.driver.get(url)
                
                # Ждем появления основных элементов
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    print("📄 Страница загружена, ожидаем успешного запроса...")
                except TimeoutException:
                    print("⚠️ Страница загружается медленно...")
                
                # Имитируем человеческие действия после загрузки
                self.simulate_human_actions()
                
                # Ждем успешного запроса и получаем статус
                success, status = self.wait_for_successful_request(url)
                
                if success:
                    print(f"✅ Страница {shop_name} успешно загружена!")
                    return True
                else:
                    print(f"❌ Не удалось получить успешный ответ для {shop_name}. Статус: {status}")
                    
                    # Обрабатываем различные типы ошибок
                    if status == 429:
                        print("⚠️ Получен код 429 (Too Many Requests)")
                        if attempt < self.max_retries - 1:
                            wait_time = 10 + (attempt * 5)  # Увеличиваем время ожидания
                            print(f"🔄 Перезагружаем страницу через {wait_time} секунд...")
                            time.sleep(wait_time)
                            self.driver.refresh()
                            # Ждем полной загрузки после перезагрузки
                            self._wait_for_page_load()
                        continue
                        
                    elif status == 403:
                        print("⚠️ Получен код 403 (Forbidden)")
                        if attempt < self.max_retries - 1:
                            print("🔄 Перезагружаем страницу через 5 секунд...")
                            time.sleep(5)
                            self.driver.refresh()
                            self._wait_for_page_load()
                        continue
                        
                    else:
                        print(f"⚠️ Неизвестная ошибка: {status}")
                        if attempt < self.max_retries - 1:
                            time.sleep(5)
                            self.driver.refresh()
                            self._wait_for_page_load()
                        continue
                    
            except WebDriverException as e:
                print(f"❌ Ошибка WebDriver: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(5)
        
        print(f"❌ Не удалось загрузить {shop_name} после {self.max_retries} попыток")
        print("🔄 Требуется перезапуск браузера")
        return False
    
    def _wait_for_page_load(self):
        """Ждет полной загрузки страницы"""
        try:
            print("⏳ Ожидание полной загрузки страницы...")
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # Дополнительная пауза для загрузки динамического контента
            time.sleep(3)
            print("✅ Страница полностью загружена")
        except TimeoutException:
            print("⚠️ Таймаут ожидания загрузки страницы")
        except Exception as e:
            print(f"⚠️ Ошибка при ожидании загрузки: {e}")
    
    def wait_for_products_and_stop_loading(self, max_wait_time: int = 30) -> bool:
        """
        Ждет появления товаров на странице и останавливает загрузку.
        Возвращает True если товары найдены, False если таймаут.
        """
        print("🛍️ Ожидание появления товаров...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Проверяем наличие контейнера с товарами
                page_source = self.driver.page_source
                if 'shop_home_listing_grid' in page_source:
                    print("✅ Контейнер с товарами найден!")
                    
                    # Останавливаем загрузку страницы
                    try:
                        self.driver.execute_script("window.stop();")
                        print("🛑 Загрузка страницы остановлена")
                    except:
                        pass
                    
                    return True
                
                # Небольшая пауза перед следующей проверкой
                time.sleep(0.5)
                
            except Exception as e:
                print(f"⚠️ Ошибка при проверке товаров: {e}")
                time.sleep(1)
        
        print(f"⏰ Таймаут ожидания товаров ({max_wait_time}s)")
        return False
    
    def _setup_request_blocking(self):
        """Настраивает блокировку ненужных запросов через selenium-wire"""
        if not SELENIUM_WIRE_AVAILABLE:
            return
        
        def request_interceptor(request):
            # Список доменов и путей для блокировки
            blocked_domains = [
                'bat.bing.com',
                'podscribe.com', 
                'googleapis.com',
                'google.com/c2dm',
                'pinterest.com',
                'qualtrics.com',
                'adsrvr.org',
                'imrworldwide.com',
                'tapad.com',
                'adnxs.com',
                'gvt2.com',
                'facebook.com',
                'doubleclick.net',
                'googlesyndication.com',
                'googletagmanager.com',
                'google-analytics.com',
                'hotjar.com',
                'mixpanel.com',
                'segment.com',
                'amplitude.com'
            ]
            
            blocked_extensions = ['.js', '.woff', '.woff2', '.ttf', '.eot']
            
            # Проверяем домен
            for domain in blocked_domains:
                if domain in request.url:
                    print(f"🚫 Блокируем запрос к {domain}")
                    request.abort()
                    return
            
            # Блокируем JS файлы (кроме основных Etsy)
            if any(request.url.endswith(ext) for ext in blocked_extensions):
                if 'etsy.com' not in request.url or '/include/tags.js' in request.url:
                    print(f"🚫 Блокируем ресурс: {request.url}")
                    request.abort()
                    return
        
        # Устанавливаем перехватчик
        self.driver.request_interceptor = request_interceptor
        print("🛡️ Настроена блокировка ненужных запросов")
    
    def get_page_source(self) -> str:
        """Возвращает HTML код страницы"""
        if not self.driver:
            return ""
        return self.driver.page_source
    
    def get_captured_headers(self) -> Dict[str, str]:
        """Возвращает захваченные headers"""
        return self.captured_headers.copy()
    
    def navigate_to_page(self, url: str) -> bool:
        """Переходит на указанную страницу"""
        try:
            self.driver.get(url)
            
            # Ждем загрузки страницы
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            return True
        except Exception as e:
            print(f"Ошибка при переходе на {url}: {e}")
            return False
    
    def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        """Ждет появления элемента на странице"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            return False
    
    def open_devtools(self):
        """Открывает DevTools программно"""
        try:
            # Открываем DevTools через F12
            self.driver.execute_script("window.open('', '_blank').close();")
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            
            # Нажимаем F12 для открытия DevTools
            ActionChains(self.driver).send_keys(Keys.F12).perform()
            time.sleep(1)
            print("🔧 DevTools открыты")
            
        except Exception as e:
            print(f"⚠️ Не удалось открыть DevTools: {e}")
    
    def close_browser(self):
        """Закрывает браузер с отладочной информацией о пагинации"""
        if self.driver:
            try:
                # Перед закрытием выводим отладочную информацию о пагинации
                self._debug_pagination_before_close()
                
                self.driver.quit()
                print("🔒 Браузер закрыт")
            except Exception as e:
                print(f"Ошибка при закрытии браузера: {e}")
            finally:
                self.driver = None
        
        # Очищаем временные файлы прокси
        self._cleanup_proxy_extension()
    
    def _debug_pagination_before_close(self):
        """Выводит отладочную информацию о пагинации перед закрытием браузера"""
        try:
            print("\n🔍 DEBUG: Проверяем пагинацию перед закрытием браузера...")
            
            html_content = self.driver.page_source
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Ищем навигацию пагинации
            pagination_nav = soup.find('nav', {'data-clg-id': 'WtPagination'})
            if pagination_nav:
                pagination_links = pagination_nav.find_all('a', class_='wt-action-group__item')
                print(f"🔍 DEBUG: Найдено {len(pagination_links)} ссылок пагинации в момент закрытия")
                
                # Находим текущую страницу
                current_page = None
                for link in pagination_links:
                    if link.get('aria-current') == 'true':
                        current_page = link.get_text(strip=True)
                        break
                
                if current_page:
                    print(f"🔍 DEBUG: Текущая страница при закрытии: {current_page}")
                    
                    # Проверяем, есть ли еще страницы
                    last_page_num = None
                    for link in pagination_links:
                        page_text = link.get_text(strip=True)
                        if page_text.isdigit():
                            last_page_num = max(last_page_num or 0, int(page_text))
                    
                    if last_page_num:
                        print(f"🔍 DEBUG: Последняя видимая страница: {last_page_num}")
                        if int(current_page) >= last_page_num:
                            print("✅ DEBUG: Действительно достигли последней страницы")
                        else:
                            print("⚠️ DEBUG: Возможно, есть еще страницы!")
                else:
                    print("⚠️ DEBUG: Не удалось определить текущую страницу")
            else:
                print("⚠️ DEBUG: Пагинация не найдена при закрытии")
                
        except Exception as e:
            print(f"⚠️ DEBUG: Ошибка при отладке пагинации: {e}")
    
    def _setup_request_blocking(self):
        """Настраивает блокировку ненужных ресурсов через selenium-wire"""
        if not SELENIUM_WIRE_AVAILABLE:
            return
            
        def request_interceptor(request):
            # Блокируемые домены и паттерны
            blocked_domains = [
                'google-analytics.com',
                'googletagmanager.com',
                'facebook.com',
                'facebook.net',
                'doubleclick.net',
                'googlesyndication.com',
                'adsystem.com',
                'amazon-adsystem.com',
                'bat.bing.com',
                'podscribe.com',
                'googleapis.com',
                'pinterest.com',
                'adsrvr.org',
                'imrworldwide.com',
                'tapad.com',
                'qualtrics.com',
                'adnxs.com',
                'gcp.gvt2.com',
                'clients.google.com'
            ]
            
            # Блокируемые типы файлов (НЕ блокируем JS - сайт требует)
            blocked_extensions = [
                '.woff',
                '.woff2',
                '.ttf',
                '.eot',
                '.svg',
                '.png',
                '.jpg',
                '.jpeg',
                '.gif',
                '.webp',
                '.ico',
                '.mp4',
                '.webm',
                '.mp3'
            ]
            
            # Проверяем домен
            for domain in blocked_domains:
                if domain in request.url:
                    print(f"🚫 Блокируем запрос к {domain}")
                    request.abort()
                    return
            
            # Проверяем расширение файла
            for ext in blocked_extensions:
                if request.url.endswith(ext):
                    print(f"🚫 Блокируем файл {ext}")
                    request.abort()
                    return
            
            # Блокируем только рекламные и трекинговые JS (разрешаем основные JS сайта)
            if any(js_pattern in request.url.lower() for js_pattern in [
                'analytics', 'tracking', 'gtag', 'fbevents', 'pixel',
                'doubleclick', 'googlesyndication', 'amazon-adsystem'
            ]) and 'etsy.com' not in request.url:
                print(f"🚫 Блокируем рекламный JS: {request.url[:100]}...")
                request.abort()
                return
                
            print(f"✅ Разрешаем: {request.url[:100]}...")
        
        # Устанавливаем перехватчик запросов
        self.driver.request_interceptor = request_interceptor
        print("🛡️ Настроена блокировка ненужных ресурсов")
    
    def restart_browser(self, change_proxy: bool = True) -> bool:
        """Перезапускает браузер (новый воркер) с возможностью смены прокси"""
        print("🔄 Перезапуск браузера...")
        self.close_browser()
        time.sleep(3)
        
        # Если нужно сменить прокси, получаем новый
        if change_proxy:
            self.current_proxy = self.proxy_manager.get_random_proxy()
            if not self.current_proxy:
                print("❌ Не удалось получить новый прокси!")
                return False
            print(f"🌐 Новый случайный прокси: {self.current_proxy['host']}:{self.current_proxy['port']}")
        
        return self.setup_driver(use_proxy=True)
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        self.close_browser()