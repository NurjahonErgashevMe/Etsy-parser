"""
Главное окно GUI приложения для Etsy Parser
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import sys
import os

from .tabs import ConfigTab, ControlTab, LogsTab

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.monitor import EtsyMonitor
from config.settings import config

logger = logging.getLogger(__name__)

class MainWindow:
    """Главное окно приложения для Etsy Parser"""
    
    def __init__(self):
        self.root = None
        self.notebook = None
        
        # Основные компоненты
        self.etsy_monitor = EtsyMonitor()
        self.telegram_bot = None
        self.bot_thread = None
        
        # Вкладки
        self.config_tab = None
        self.control_tab = None
        self.logs_tab = None
        
        # Устанавливаем статус запуска
        try:
            from utils.config_loader import config_loader
            config_loader.set_working_status("start")
            logger.info("Статус парсера установлен в 'start'")
        except Exception as e:
            logger.error(f"Ошибка установки статуса запуска: {e}")
        
        logger.info("Etsy Parser GUI инициализирован")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.root = tk.Tk()
            self.root.title("🛍️ Etsy Parser & Bot Manager v1.0")
            self.root.geometry("1000x750")
            self.root.minsize(900, 650)
            
            # Центрирование окна
            self.root.eval('tk::PlaceWindow . center')
            
            # Обработчик закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            self._create_widgets()
            self._start_status_updater()
            
            logger.info("Etsy Parser GUI запущен")
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Ошибка GUI: {e}")
            messagebox.showerror("Ошибка", f"Критическая ошибка GUI: {e}")
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создаем вкладки
        self.config_tab = ConfigTab(self.notebook, self)
        self.control_tab = ControlTab(self.notebook, self)
        self.logs_tab = LogsTab(self.notebook, self)
        
        # Добавляем вкладки в notebook
        self.notebook.add(self.config_tab.get_frame(), text="⚙️ Конфигурация")
        self.notebook.add(self.control_tab.get_frame(), text="🤖 Telegram Бот")
        self.notebook.add(self.logs_tab.get_frame(), text="📝 Логи")
        
        # Статусная строка
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
    

    

    

    

    
    def _start_status_updater(self):
        """Запуск обновления статуса"""
        def update_status():
            try:
                # Обновляем статус в вкладке управления
                if self.control_tab:
                    self.control_tab.update_status()
                
                # Обновляем статусную строку
                if (self.telegram_bot and 
                    self.telegram_bot.is_running() and 
                    self.bot_thread and 
                    self.bot_thread.is_alive()):
                    self.status_var.set("🤖 Telegram бот активен")
                else:
                    self.status_var.set("✅ Готов к работе")
                
            except Exception as e:
                logger.debug(f"Ошибка обновления статуса: {e}")
            
            # Планируем следующее обновление
            if self.root:
                self.root.after(3000, update_status)
        
        # Запускаем первое обновление
        self.root.after(1000, update_status)
    
    def get_config_data(self):
        """Получение данных конфигурации из вкладки"""
        if self.config_tab:
            # Собираем все User ID из массива
            user_ids = []
            for var in self.config_tab.user_id_vars:
                user_id = var.get().strip()
                if user_id:  # Добавляем только непустые ID
                    user_ids.append(user_id)
            
            return {
                'bot_token': self.config_tab.bot_token_var.get().strip(),
                'user_ids': user_ids,  # Возвращаем массив ID
                'user_id': user_ids[0] if user_ids else ''  # Для обратной совместимости
            }
        return {}
    
    
    
    def _on_closing(self):
        try:
            logger.info("Закрытие Etsy Parser...")

            # Устанавливаем статус остановки в config.txt
            try:
                from utils.config_loader import config_loader
                config_loader.set_working_status("stop")
                logger.info("Статус парсера установлен в 'stop'")
            except Exception as e:
                logger.error(f"Ошибка установки статуса остановки: {e}")

            # Закрываем окно сразу
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Ошибка закрытия: {e}")
            self.root.destroy()