"""
Парсер для магазинов Etsy с использованием Selenium Stealth
Включает автоматическую обработку 403 ошибок:
- При получении 403 ответа ждет 10 секунд и перезагружает страницу
- После 3 неудачных попыток закрывает браузер и запускает новый
- Продолжает парсинг с той же ссылки, а не переходит к следующему магазину
"""
import re
import time
from typing import List, Optional
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser
from models.product import Product
from services.browser_service import BrowserService

class EtsyParser(BaseParser):
    """Парсер для магазинов Etsy только через браузер"""
    
    def __init__(self, config):
        super().__init__(config)
        self.browser_service = None
    
    def get_shop_name_from_url(self, url: str) -> str:
        """Извлекает название магазина из URL"""
        try:
            # Для URL вида https://www.etsy.com/shop/PiondressShop
            match = re.search(r'/shop/([^/?]+)', url)
            if match:
                return match.group(1)
            return "unknown_shop"
        except:
            return "unknown_shop"
    
    def parse_shop_page(self, shop_url: str) -> List[Product]:
        """Парсит все страницы магазина с пагинацией через браузер"""
        all_products = []
        current_url = shop_url
        page_num = 1
        browser_restart_count = 0
        max_browser_restarts = 3
        
        # Инициализируем браузер
        if not self._initialize_browser():
            return []
        
        # Загружаем первую страницу
        if not self._load_first_page_with_browser_retry(shop_url):
            print("❌ Не удалось загрузить первую страницу после всех попыток")
            return []
        
        # Теперь парсим все страницы
        while current_url:
            print(f"📄 Парсим страницу {page_num}: {current_url}")
            
            # Парсим текущую страницу с обработкой ошибок
            products = self._parse_single_page_with_retry(current_url, page_num == 1)
            
            if products is None:  # Требуется перезапуск браузера
                if browser_restart_count < max_browser_restarts:
                    browser_restart_count += 1
                    print(f"🔄 Перезапуск браузера #{browser_restart_count}/{max_browser_restarts}")
                    
                    if self._restart_browser_and_continue(current_url):
                        print("✅ Браузер перезапущен, продолжаем с текущей страницы")
                        continue  # Повторяем попытку с той же страницей
                    else:
                        print("❌ Не удалось перезапустить браузер")
                        break
                else:
                    print(f"❌ Превышено максимальное количество перезапусков браузера ({max_browser_restarts})")
                    break
            elif products:
                all_products.extend(products)
                print(f"✅ Найдено товаров на странице {page_num}: {len(products)}")
                browser_restart_count = 0  # Сбрасываем счетчик при успешном парсинге
                
                # Получаем URL следующей страницы
                next_url = self._get_next_page_url_from_browser()
                if next_url:
                    current_url = next_url
                    page_num += 1
                    # Минимальная пауза между страницами
                    time.sleep(1)
                else:
                    print("📋 Следующая страница не найдена, завершаем парсинг")
                    break
            else:
                print(f"⚠️ Товары не найдены на странице {page_num}")
                break
        
        print(f"🎉 Всего найдено товаров: {len(all_products)} на {page_num} страницах")
        
        # Закрываем браузер
        if self.browser_service:
            # self.browser_service.close_browser()
            self.browser_service = None
        
        return all_products
    
    def _initialize_browser(self) -> bool:
        """Инициализирует браузер с повторными попытками"""
        if not self.browser_service:
            self.browser_service = BrowserService(self.config)
            
        # Пытаемся запустить браузер с повторными попытками
        for attempt in range(3):
            if self.browser_service.setup_driver():
                return True
            else:
                print(f"❌ Попытка {attempt + 1}/3 запуска браузера не удалась")
                if attempt < 2:
                    time.sleep(2)
                    self.browser_service.restart_browser()
                else:
                    print("❌ Не удалось запустить браузер после 3 попыток")
                    return False
        return False
    
    def _load_first_page_with_browser_retry(self, shop_url: str) -> bool:
        """Загружает первую страницу с обработкой 403 ошибок и перезапуском браузера при необходимости"""
        max_browser_restarts = 3
        
        for browser_restart in range(max_browser_restarts):
            print(f"🚀 Попытка загрузки первой страницы (перезапуск браузера {browser_restart + 1}/{max_browser_restarts})")
            
            # Используем новый метод с обработкой 403
            success, need_browser_restart = self.browser_service.load_page_with_403_handling(shop_url)
            
            if success:
                print("✅ Первая страница успешно загружена")
                return True
            elif need_browser_restart:
                print(f"🔄 Требуется перезапуск браузера (попытка {browser_restart + 1}/{max_browser_restarts})")
                if browser_restart < max_browser_restarts - 1:
                    if not self.browser_service.restart_browser():
                        print("❌ Не удалось перезапустить браузер")
                        return False
                    time.sleep(2)
                else:
                    print("❌ Превышено максимальное количество перезапусков браузера")
                    return False
            else:
                print("❌ Не удалось загрузить первую страницу")
                return False
        
        return False
    
    def _parse_single_page_with_retry(self, page_url: str, is_first_page: bool = False) -> Optional[List[Product]]:
        """Парсит страницу с обработкой ошибок. Возвращает None если нужен перезапуск браузера"""
        try:
            return self._parse_single_page_with_browser(page_url, is_first_page)
        except Exception as e:
            print(f"❌ Критическая ошибка при парсинге страницы: {e}")
            return None  # Сигнал для перезапуска браузера
    
    def _restart_browser_and_continue(self, current_url: str) -> bool:
        """Перезапускает браузер и продолжает с указанной страницы"""
        if not self.browser_service.restart_browser():
            return False
        
        # Загружаем текущую страницу в новом браузере с обработкой 403
        success, need_browser_restart = self.browser_service.load_page_with_403_handling(current_url)
        
        if success:
            return True
        elif need_browser_restart:
            print("❌ Получен 403 даже после перезапуска браузера")
            return False
        else:
            print("❌ Не удалось загрузить страницу после перезапуска браузера")
            return False
    
    def _load_first_page_with_browser(self, shop_url: str) -> bool:
        """Загружает первую страницу через браузер"""
        print(f"🌐 Загружаем первую страницу через браузер: {shop_url}")
        
        # Пытаемся загрузить страницу с повторными попытками
        if self.browser_service.load_page_with_retries(shop_url):
            print("✅ Первая страница успешно загружена")
            return True
        else:
            # Пробуем перезапустить браузер
            print("🔄 Пытаемся перезапустить браузер...")
            if self.browser_service.restart_browser():
                return self.browser_service.load_page_with_retries(shop_url)
            
        return False
    
    def _parse_single_page_with_browser(self, page_url: str, is_first_page: bool = False) -> List[Product]:
        """Парсит одну страницу магазина только через браузер"""
        # Если это не первая страница, переходим на нужную страницу с обработкой 403
        if not is_first_page:
            if page_url != self.browser_service.driver.current_url:
                success, need_browser_restart = self.browser_service.load_page_with_403_handling(page_url)
                if not success:
                    if need_browser_restart:
                        print(f"❌ Получен 403 при переходе на страницу: {page_url}")
                        return None  # Сигнал для перезапуска браузера
                    else:
                        print(f"❌ Не удалось перейти на страницу: {page_url}")
                        return []
                time.sleep(1)  # Быстрая загрузка
        
        # Проверяем на блокировку и обрабатываем её (дополнительная проверка)
        if not self._handle_blocking_with_retries(page_url):
            print("❌ Не удалось обойти блокировку после всех попыток")
            return None  # Сигнал для перезапуска браузера
        
        # Получаем HTML контент из браузера
        html_content = self.browser_service.get_page_source()
        
        if not html_content:
            print("❌ Не удалось получить HTML контент")
            return []
        
        # Парсим HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Ищем контейнер с товарами
        listing_grid = soup.find('div', {'data-appears-component-name': 'shop_home_listing_grid'})
        
        if not listing_grid:
            print("⚠️ Не найден контейнер с товарами")
            return []
        
        # Ищем все ссылки с data-listing-id
        listing_links = listing_grid.find_all('a', {'data-listing-id': True})
        
        products = []
        shop_name = self.get_shop_name_from_url(page_url)
        
        for link in listing_links:
            try:
                product = self._parse_product_element(link, shop_name)
                if product:
                    products.append(product)
                    
            except Exception as e:
                print(f"❌ Ошибка при парсинге товара: {e}")
                continue
        
        # После парсинга товаров делаем плавный скролл к пагинации
        self._scroll_to_pagination()
        
        return products
    
    def _handle_blocking_with_retries(self, page_url: str) -> bool:
        """Проверяет на блокировку. При обнаружении блокировки сразу требует перезапуск браузера"""
        if self._check_for_blocking():
            print("🚫 БЛОКИРОВКА ОБНАРУЖЕНА! Перезагрузка страницы не поможет")
            print("🔄 Требуется перезапуск браузера с новым IP/сессией")
            return False  # Сигнал для перезапуска браузера
        else:
            # Блокировки нет, все в порядке
            return True
    
    def _check_for_blocking(self) -> bool:
        """Проверяет HTML страницы на наличие сообщений о блокировке"""
        try:
            html_content = self.browser_service.get_page_source()
            if not html_content:
                return False
            
            page_source = html_content.lower()
            
            # Расширенный список фраз, указывающих на блокировку
            blocking_phrases = [
                'Вы были заблокированы',
                'you have been blocked',
                'access denied',
                'нечто в поведении браузера нас насторожило',
                'что-то блокирует работу javascript',
                'находится робот',
                'сверхчеловеческой скоростью',
                'something about your browser made us think',
                'robot in the same network',
                'blocking javascript',
                'superhuman speed'
            ]
            
            # Проверяем фразы блокировки
            for phrase in blocking_phrases:
                if phrase in page_source:
                    print(f"🚫 БЛОКИРОВКА ОБНАРУЖЕНА! Найдена фраза: '{phrase}'")
                    return True
            
            # Дополнительная проверка на отсутствие основного контента
            if 'shop_home_listing_grid' not in page_source and len(page_source) < 10000:
                print("🚫 Подозрение на блокировку: слишком мало контента и нет основных элементов")
                return True
            
            print("✅ Признаков блокировки не обнаружено")
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка при проверке блокировки: {e}")
            return False
    
    def _get_next_page_url_from_browser(self) -> Optional[str]:
        """Получает URL следующей страницы из пагинации через браузер"""
        if not self.browser_service or not self.browser_service.driver:
            return None
        
        html_content = self.browser_service.get_page_source()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Ищем навигацию пагинации
        pagination_nav = soup.find('nav', {'data-clg-id': 'WtPagination'})
        if not pagination_nav:
            print("📋 Пагинация не найдена")
            return None
        
        # Ищем все ссылки пагинации
        pagination_links = pagination_nav.find_all('a', class_='wt-action-group__item')
        
        print(f"🔍 DEBUG: Найдено {len(pagination_links)} ссылок пагинации")
        
        # Выводим отладочную информацию о всех ссылках
        for i, link in enumerate(pagination_links):
            page_num = link.get_text(strip=True)
            data_page = link.get('data-page')
            aria_current = link.get('aria-current')
            href = link.get('href')
            is_disabled = 'wt-is-disabled' in link.get('class', [])
            
            print(f"🔍 DEBUG: Ссылка {i}: текст='{page_num}', data-page='{data_page}', aria-current='{aria_current}', disabled={is_disabled}")
        
        # Находим текущую страницу (с aria-current="true")
        current_page_found = False
        current_page_index = -1
        
        for i, link in enumerate(pagination_links):
            if link.get('aria-current') == 'true':
                current_page_found = True
                current_page_index = i
                current_page_text = link.get_text(strip=True)
                print(f"✅ DEBUG: Найдена текущая страница {current_page_text} на позиции {i}")
                
                # Проверяем, есть ли следующая ссылка
                if i + 1 < len(pagination_links):
                    next_link = pagination_links[i + 1]
                    next_href = next_link.get('href')
                    next_page_text = next_link.get_text(strip=True)
                    is_next_disabled = 'wt-is-disabled' in next_link.get('class', [])
                    
                    print(f"🔍 DEBUG: Следующая ссылка: текст='{next_page_text}', disabled={is_next_disabled}")
                    
                    if next_href and next_link.get('data-page') and not is_next_disabled:
                        # Формируем полный URL
                        if next_href.startswith('http'):
                            print(f"➡️ Найдена следующая страница: {next_href}")
                            return next_href
                        else:
                            full_url = f"https://www.etsy.com{next_href}"
                            print(f"➡️ Найдена следующая страница: {full_url}")
                            return full_url
                    else:
                        print(f"⚠️ DEBUG: Следующая ссылка недоступна (href={bool(next_href)}, data-page={bool(next_link.get('data-page'))}, disabled={is_next_disabled})")
                else:
                    print("⚠️ DEBUG: Текущая страница последняя в списке")
                break
        
        # Если текущая страница не найдена, ищем кнопку "Следующая страница"
        if not current_page_found:
            print("⚠️ DEBUG: Текущая страница не найдена, ищем кнопку 'Следующая страница'")
            for i, link in enumerate(pagination_links):
                if link.get('data-page'):
                    # Проверяем, это ли кнопка "следующая"
                    screen_reader_text = link.find('span', class_='wt-screen-reader-only')
                    if screen_reader_text:
                        sr_text = screen_reader_text.get_text()
                        print(f"🔍 DEBUG: Screen reader текст ссылки {i}: '{sr_text}'")
                        
                        if 'Следующая страница' in sr_text or 'Next page' in sr_text:
                            next_href = link.get('href')
                            is_disabled = 'wt-is-disabled' in link.get('class', [])
                            
                            if next_href and not is_disabled:
                                if next_href.startswith('http'):
                                    print(f"➡️ Найдена следующая страница через кнопку: {next_href}")
                                    return next_href
                                else:
                                    full_url = f"https://www.etsy.com{next_href}"
                                    print(f"➡️ Найдена следующая страница через кнопку: {full_url}")
                                    return full_url
                            else:
                                print(f"⚠️ DEBUG: Кнопка 'Следующая страница' отключена или без href")
        
        print("📋 DEBUG: Следующая страница действительно не найдена - это последняя страница")
        return None
    
    def _scroll_to_pagination(self):
        """Быстрый скролл к блоку пагинации"""
        try:
            if not self.browser_service or not self.browser_service.driver:
                return
            
            print("🖱️ Быстрый скролл к пагинации...")
            
            # Ищем элемент пагинации и скроллим мгновенно
            pagination_script = """
                var paginationDiv = document.querySelector('div[data-item-pagination]');
                if (paginationDiv) {
                    // Получаем позицию элемента
                    var rect = paginationDiv.getBoundingClientRect();
                    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    var targetPosition = rect.top + scrollTop - 200;
                    
                    // Мгновенный скролл
                    window.scrollTo(0, targetPosition);
                    return true;
                } else {
                    // Если основной элемент не найден, ищем nav внутри
                    var navPagination = document.querySelector('nav[data-clg-id="WtPagination"]');
                    if (navPagination) {
                        var rect = navPagination.getBoundingClientRect();
                        var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                        var targetPosition = rect.top + scrollTop - 20;
                        
                        window.scrollTo(0, targetPosition);
                        return true;
                    } else {
                        // Если пагинация не найдена, скроллим вниз страницы
                        window.scrollTo(0, document.body.scrollHeight * 0.8);
                        return false;
                    }
                }
            """
            
            # Выполняем скрипт
            pagination_found = self.browser_service.driver.execute_script(pagination_script)
            
            if pagination_found:
                print("✅ Быстрый скролл к пагинации выполнен")
            else:
                print("⚠️ Пагинация не найдена, выполнен скролл вниз страницы")
            
            # Минимальное ожидание загрузки пагинации
            time.sleep(0.5)
            
        except Exception as e:
            print(f"⚠️ Ошибка при скролле к пагинации: {e}")
    
    def _parse_product_element(self, link_element, shop_name: str) -> Product:
        """Парсит элемент товара"""
        listing_id = link_element.get('data-listing-id')
        product_url = link_element.get('href')
        
        # Получаем название товара из title или из h3
        title = link_element.get('title')
        if not title:
            title_element = link_element.find('h3')
            title = title_element.get_text(strip=True) if title_element else "Без названия"
        
        # Формируем полную ссылку если нужно
        if product_url and not product_url.startswith('http'):
            product_url = 'https://www.etsy.com' + product_url
        
        # Пытаемся найти цену
        price = None
        currency = None
        price_element = link_element.find('span', class_='currency-value')
        if price_element:
            price = price_element.get_text(strip=True)
            currency_element = link_element.find('span', class_='currency-symbol')
            if currency_element:
                currency = currency_element.get_text(strip=True)
        
        # Пытаемся найти изображение
        image_url = None
        img_element = link_element.find('img')
        if img_element:
            image_url = img_element.get('src')
        
        return Product(
            listing_id=listing_id,
            title=title,
            url=product_url,
            shop_name=shop_name,
            price=price,
            currency=currency,
            image_url=image_url
        )