"""
Вкладка управления Telegram ботом
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
import time
import asyncio

logger = logging.getLogger(__name__)

class ControlTab:
    """Вкладка управления Telegram ботом"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        
        # Переменные статуса
        self.bot_status_var = tk.StringVar(value="🔴 Не запущен")
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов вкладки"""
        self.frame = ttk.Frame(self.parent)
        
        # Статус
        status_group = ttk.LabelFrame(self.frame, text="📊 Статус Telegram бота", padding=15)
        status_group.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(status_group, text="Telegram бот:", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(status_group, textvariable=self.bot_status_var, font=('Arial', 14)).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Управление ботом
        bot_group = ttk.LabelFrame(self.frame, text="🤖 Управление Telegram ботом", padding=15)
        bot_group.pack(fill=tk.X, padx=10, pady=20)
        
        bot_buttons_frame = ttk.Frame(bot_group)
        bot_buttons_frame.pack(fill=tk.X)
        
        self.start_bot_btn = ttk.Button(bot_buttons_frame, text="▶️ Запустить бота", 
                                       command=self._start_bot)
        self.start_bot_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_bot_btn = ttk.Button(bot_buttons_frame, text="⏹️ Остановить бота", 
                                      command=self._stop_bot, state=tk.DISABLED)
        self.stop_bot_btn.pack(side=tk.LEFT, padx=5)
        
        self.restart_bot_btn = ttk.Button(bot_buttons_frame, text="🔄 Перезапустить бота", 
                                         command=self._restart_bot, state=tk.DISABLED)
        self.restart_bot_btn.pack(side=tk.LEFT, padx=5)
        

        

    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def update_status(self):
        """Обновление статуса бота"""
        try:
            # Проверяем статус бота
            if (self.main_window.telegram_bot and 
                self.main_window.telegram_bot.is_running() and 
                self.main_window.bot_thread and 
                self.main_window.bot_thread.is_alive()):
                self.bot_status_var.set("🟢 Запущен")
                self.start_bot_btn.config(state=tk.DISABLED)
                self.stop_bot_btn.config(state=tk.NORMAL)
                self.restart_bot_btn.config(state=tk.NORMAL)
            else:
                self.bot_status_var.set("🔴 Не запущен")
                self.start_bot_btn.config(state=tk.NORMAL)
                self.stop_bot_btn.config(state=tk.DISABLED)
                self.restart_bot_btn.config(state=tk.DISABLED)
                
        except Exception as e:
            logger.debug(f"Ошибка обновления статуса: {e}")
    

    

    

    
    def _start_bot(self):
        """Запуск Telegram бота"""
        def start_async():
            try:
                config = self.main_window.config_tab.get_config_data()
                bot_token = config.get('bot_token')
                user_ids = config.get('user_ids', [])
                
                if not bot_token or not user_ids:
                    messagebox.showerror("Ошибка", "Настройте токен бота и User ID на вкладке 'Конфигурация'")
                    return
                
                # Импортируем и создаем бота
                from bot.gui_integration import TelegramBotGUI
                
                self.main_window.telegram_bot = TelegramBotGUI(bot_token, user_ids)
                
                # Запускаем бота в отдельном потоке
                def run_bot():
                    try:
                        asyncio.run(self.main_window.telegram_bot.start())
                    except Exception as e:
                        logger.error(f"Ошибка работы бота: {e}")
                
                self.main_window.bot_thread = threading.Thread(target=run_bot, daemon=True)
                self.main_window.bot_thread.start()
                
                # Даем время боту запуститься
                time.sleep(2)
                
                self.update_status()
                messagebox.showinfo("Успех", "Telegram бот запущен")
                    
            except Exception as e:
                logger.error(f"Ошибка запуска бота: {e}")
                messagebox.showerror("Ошибка", f"Ошибка запуска бота: {e}")
        
        threading.Thread(target=start_async, daemon=True).start()
    
    def _stop_bot(self):
        """Остановка Telegram бота"""
        try:
            if self.main_window.telegram_bot:
                # Останавливаем бота
                asyncio.run(self.main_window.telegram_bot.stop())
                self.main_window.telegram_bot = None
                self.main_window.bot_thread = None
            
            self.update_status()
            messagebox.showinfo("Успех", "Telegram бот остановлен")
            
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            messagebox.showerror("Ошибка", f"Ошибка остановки бота: {e}")
    
    def _restart_bot(self):
        """Перезапуск Telegram бота"""
        def restart_async():
            try:
                # Сначала останавливаем
                self._stop_bot()
                
                # Ждем немного
                time.sleep(2)
                
                # Затем запускаем
                self._start_bot()
                
            except Exception as e:
                logger.error(f"Ошибка перезапуска бота: {e}")
                messagebox.showerror("Ошибка", f"Ошибка перезапуска бота: {e}")
        
        if messagebox.askyesno("Подтверждение", "Перезапустить Telegram бота?"):
            threading.Thread(target=restart_async, daemon=True).start()
    

    
