"""
Сервис для работы с браузером через Selenium Stealth
"""
import time
import json
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class BrowserService:
    """Сервис для работы с браузером"""
    
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.captured_headers = {}
        self.max_retries = 3
        self.wait_timeout = 90  # 1.5 минуты
        
    def setup_driver(self):
        """Настройка Chrome драйвера с stealth режимом и имитацией человека"""
        chrome_options = Options()
        
        # Основные опции для stealth режима
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Открываем браузер в полноэкранном режиме
        chrome_options.add_argument("--start-maximized")
        
        # Убираем автоматическое открытие DevTools (вызывает проблемы с загрузкой)
        # chrome_options.add_argument("--auto-open-devtools-for-tabs")
        
        # Настройки для имитации человека
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Отключаем изображения для скорости
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.media_stream": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Включаем логирование сетевых запросов
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # Дополнительные опции для стабильности
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        # Убираем конфликтующие опции
        # chrome_options.add_argument("--disable-images")  # Уже отключены через prefs
        # chrome_options.add_argument("--disable-javascript")  # JS нужен для работы сайта
        
        # Убираем проблемные опции
        # chrome_options.add_argument("--disable-web-security")
        # chrome_options.add_argument("--allow-running-insecure-content")
        
        try:
            # Автоматическая установка ChromeDriver
            service = Service(ChromeDriverManager().install())
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
            
            print("✅ Браузер успешно запущен в stealth режиме с имитацией человека")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при запуске браузера: {e}")
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
            
            print("🤖 Настроена имитация человеческого поведения")
            
        except Exception as e:
            print(f"⚠️ Ошибка при настройке имитации человека: {e}")
    
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
        
        while time.time() - start_time < self.wait_timeout:
            try:
                # Получаем логи производительности
                logs = self.driver.get_log('performance')
                
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
                    print("📄 Страница загружена, ожидаем успешного запроса...")
                except TimeoutException:
                    print("⚠️ Страница загружается медленно...")
                
                # Имитируем человеческие действия после загрузки
                self.simulate_human_actions()
                
                # Ждем успешного запроса и получаем статус
                success, status = self.wait_for_successful_request(url)
                
                if success:
                    print(f"✅ Страница {shop_name} успешно загружена!")
                    return True, False
                elif status == 403:
                    print(f"🚫 Получен 403 для {shop_name} (попытка {attempt + 1}/{max_403_retries})")
                    
                    if attempt < max_403_retries - 1:
                        print("🔄 Перезагружаем страницу через 5 секунд (возможно капча)...")
                        time.sleep(5)
                        self.driver.refresh()
                        self._wait_for_page_load()
                        continue
                    else:
                        print("❌ Получен 403 после 3 попыток - требуется новый браузер")
                        return False, True
                else:
                    # Другие ошибки
                    print(f"❌ Получен статус {status} для {shop_name}")
                    return False, False
                    
            except WebDriverException as e:
                print(f"❌ Ошибка WebDriver: {e}")
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
    
    def restart_browser(self) -> bool:
        """Перезапускает браузер (новый воркер)"""
        print("🔄 Перезапуск браузера...")
        self.close_browser()
        time.sleep(3)
        return self.setup_driver()
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        self.close_browser()