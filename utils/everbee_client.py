"""
EverBee API клиент для получения аналитики по листингам
"""
import json
import logging
import requests
from typing import Optional, Dict, List
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class EverBeeClient:
    """Клиент для работы с EverBee API"""
    
    AUTH_URL = "https://auth.everbee.io/login"
    LOGIN_REQUEST_URL = "https://auth.everbee.com/oauth/token"
    SHOW_USER_URL = "https://api.everbee.com/users/show"
    LISTING_DETAILS_URL = "https://api.everbee.com/listings/{listing_id}"
    LISTINGS_BATCH_URL = "https://api.everbee.com/etsy_apis/listing"
    SHOP_ANALYZE_URL = "https://api.everbee.com/shops/analyze_shop"
    
    def __init__(self, config_path: str = "config-main.txt"):
        self.config_path = config_path
        self.token = None
        self.username = None
        self.password = None
        self._load_config()
    
    def _load_config(self):
        """Загружает конфигурацию из файла"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('EVERBEE_TOKEN='):
                        self.token = line.replace('EVERBEE_TOKEN=', '')
                    elif line.startswith('EVERBEE_USERNAME='):
                        self.username = line.replace('EVERBEE_USERNAME=', '')
                    elif line.startswith('EVERBEE_PASSWORD='):
                        self.password = line.replace('EVERBEE_PASSWORD=', '')
        except FileNotFoundError:
            logging.warning(f"Конфиг файл {self.config_path} не найден")
    
    def _save_token(self, token: str):
        """Сохраняет токен в конфиг файл"""
        try:
            lines = []
            token_exists = False
            
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except FileNotFoundError:
                pass
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.startswith('EVERBEE_TOKEN='):
                        f.write(f'EVERBEE_TOKEN={token}\n')
                        token_exists = True
                    else:
                        f.write(line)
                
                if not token_exists:
                    f.write(f'EVERBEE_TOKEN={token}\n')
            
            self.token = token
            logging.info("Токен EverBee сохранен")
            
        except Exception as e:
            logging.error(f"Ошибка сохранения токена: {e}")
    
    def check_token_valid(self, token: Optional[str] = None) -> bool:
        """Проверяет валидность токена"""
        check_token = token or self.token
        
        if not check_token:
            return False
        
        headers = {'x-access-token': check_token}
        
        try:
            response = requests.get(self.SHOW_USER_URL, headers=headers, timeout=10)
            is_valid = response.status_code == 200
            
            if is_valid:
                logging.info("Токен EverBee валиден")
            else:
                logging.warning(f"Токен невалиден: {response.status_code}")
            
            return is_valid
            
        except Exception as e:
            logging.error(f"Ошибка проверки токена: {e}")
            return False
    
    def _authorize_and_get_token(self) -> Optional[str]:
        """Авторизуется на EverBee и получает токен"""
        if not self.username or not self.password:
            logging.error("Не указаны EVERBEE_USERNAME или EVERBEE_PASSWORD в конфиге")
            return None
        
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = None

        logging.info(f"Авторизация EverBee для пользователя: {self.username}")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.AUTH_URL)
            
            wait = WebDriverWait(driver, 15)
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_field = driver.find_element(By.ID, "password")
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            # Очищаем поля и заполняем
            import time
            from selenium.webdriver.common.keys import Keys
            
            # Очищаем поле email и заполняем
            email_field.click()
            email_field.send_keys(Keys.CONTROL + "a")
            email_field.send_keys(Keys.DELETE)
            time.sleep(0.5)
            email_field.send_keys(self.username)
            
            # Очищаем поле password и заполняем
            password_field.click()
            password_field.send_keys(Keys.CONTROL + "a")
            password_field.send_keys(Keys.DELETE)
            time.sleep(0.5)
            password_field.send_keys(self.password)
            
            # Пауза перед отправкой
            time.sleep(1)
            
            submit_btn.click()
            
            wait.until(lambda d: d.current_url != self.AUTH_URL)
            
            for request in driver.requests:
                if request.url == self.LOGIN_REQUEST_URL and request.method == 'POST':
                    if request.response:
                        response_body = request.response.body.decode('utf-8')
                        response_data = json.loads(response_body)
                        token = response_data.get('access_token')
                        
                        if token:
                            logging.info("Токен EverBee получен")
                            return token
            
            logging.error("Токен не найден в запросах")
            return None
            
        except Exception as e:
            logging.error(f"Ошибка авторизации EverBee: {e}")
            return None
            
        finally:
            if driver:
                driver.quit()
    
    def ensure_token(self) -> bool:
        """Проверяет токен и получает новый при необходимости"""
        if self.token and self.check_token_valid():
            return True
        
        logging.info("Получение нового токена EverBee...")
        new_token = self._authorize_and_get_token()
        
        if new_token:
            self._save_token(new_token)
            return True
        
        return False
    
    def get_listings_batch(self, listing_ids: List[str]) -> Optional[Dict]:
        """Получает данные нескольких листингов одним запросом"""
        if not self.ensure_token():
            logging.error("Не удалось получить валидный токен")
            return None
        
        headers = {'x-access-token': self.token}
        
        try:
            response = requests.post(
                self.LISTINGS_BATCH_URL, 
                headers=headers, 
                json={"listing_ids": listing_ids},
                timeout=30
            )
            
            if response.status_code == 401:
                logging.warning("Токен недействителен, получаем новый...")
                if self.refresh_token():
                    headers = {'x-access-token': self.token}
                    response = requests.post(
                        self.LISTINGS_BATCH_URL, 
                        headers=headers, 
                        json={"listing_ids": listing_ids},
                        timeout=30
                    )
                else:
                    logging.error("Не удалось обновить токен")
                    return None
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Ошибка получения данных листингов: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Ошибка запроса к EverBee: {e}")
            return None
    
    def extract_listing_data(self, listing: Dict) -> Dict:
        """Извлекает нужные поля из данных листинга"""
        return {
            "price": listing.get("price"),
            "est_total_sales": listing.get("est_total_sales"),
            "est_mo_sales": listing.get("est_mo_sales"),
            "listing_age_in_months": listing.get("listing_age_in_months"),
            "est_reviews": listing.get("est_reviews"),
            "est_reviews_in_months": listing.get("est_reviews_in_months"),
            "conversion_rate": listing.get("conversion_rate"),
            "views": listing.get("views"),
            "num_favorers": listing.get("num_favorers"),
            "url": listing.get("url")
        }
    
    def get_shop_listings(self, shop_name: str, order_by: str = "listing_age_in_months", 
                           time_range: str = "last_1_month", order_direction: str = "asc", 
                           page: int = 1, per_page: int = 20) -> Optional[Dict]:
        """Получает листинги магазина с сортировкой"""
        if not self.ensure_token():
            logging.error("Не удалось получить валидный токен")
            return None
        
        headers = {'x-access-token': self.token}
        params = {
            'shop_name': shop_name,
            'order_by': order_by,
            'time_range': time_range,
            'order_direction': order_direction,
            'page': page,
            'per_page': per_page
        }
        
        try:
            response = requests.get(
                self.SHOP_ANALYZE_URL, 
                headers=headers, 
                params=params,
                timeout=30
            )
            
            if response.status_code == 401:
                logging.warning(f"Токен недействителен для магазина {shop_name}, получаем новый...")
                if self.refresh_token():
                    headers = {'x-access-token': self.token}
                    response = requests.get(
                        self.SHOP_ANALYZE_URL, 
                        headers=headers, 
                        params=params,
                        timeout=30
                    )
                else:
                    logging.error("Не удалось обновить токен")
                    return None
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Ошибка получения листингов магазина {shop_name}: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Ошибка запроса к EverBee для магазина {shop_name}: {e}")
            return None
    
    def refresh_token(self) -> bool:
        """Принудительно обновляет токен"""
        logging.info("Принудительное обновление токена EverBee...")
        new_token = self._authorize_and_get_token()
        
        if new_token:
            self._save_token(new_token)
            return True
        
        return False
