"""
Вкладка конфигурации для Etsy Parser
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from pathlib import Path
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config_loader import config_loader

logger = logging.getLogger(__name__)

class ConfigTab:
    """Вкладка настроек Telegram бота"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        
        # Переменные
        self.bot_token_var = tk.StringVar()
        self.show_token_var = tk.BooleanVar()
        
        # Массив для пользователей (максимум 3)
        self.user_id_vars = []
        self.user_id_entries = []
        self.remove_buttons = []
        self.max_users = 3
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов вкладки"""
        self.frame = ttk.Frame(self.parent)
        
        # Telegram настройки
        telegram_group = ttk.LabelFrame(self.frame, text="🤖 Настройки Telegram бота для уведомлений", padding=15)
        telegram_group.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(telegram_group, text="Токен бота:", font=('Arial', 12)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.token_entry = ttk.Entry(telegram_group, textvariable=self.bot_token_var, width=60, show="*")
        self.token_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        show_token_cb = ttk.Checkbutton(telegram_group, text="Показать токен", 
                                       variable=self.show_token_var, 
                                       command=self._toggle_token_visibility)
        show_token_cb.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Контейнер для пользователей
        ttk.Label(telegram_group, text="User IDs:", font=('Arial', 12)).grid(row=2, column=0, sticky=tk.NW, pady=5)
        
        self.users_frame = ttk.Frame(telegram_group)
        self.users_frame.grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # Кнопка добавления пользователя
        self.add_user_btn = ttk.Button(telegram_group, text="➕ Добавить ID", command=self._add_user_field)
        self.add_user_btn.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        telegram_group.columnconfigure(1, weight=1)
        
        # Добавляем первое поле по умолчанию
        self._add_user_field()
        
        # Кнопки
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=15)
        
        ttk.Button(buttons_frame, text="💾 Сохранить", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="📁 Загрузить", command=self._load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🗑️ Очистить", command=self._clear_fields).pack(side=tk.LEFT, padx=5)
        
        # Информация
        info_frame = ttk.LabelFrame(self.frame, text="📋 Как получить данные", padding=15)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = """1. Создайте бота через @BotFather в Telegram:
   • Отправьте команду /newbot
   • Следуйте инструкциям и получите токен

2. Узнайте свой User ID:
   • Напишите боту @userinfobot
   • Или найдите свой ID через @getmyid_bot

3. Введите полученные данные в поля выше
4. Нажмите 'Сохранить' для сохранения настроек

Бот будет отправлять уведомления о новых товарах в Etsy магазинах."""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, font=('Arial', 10))
        info_label.pack(anchor=tk.W)
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def _toggle_token_visibility(self):
        """Переключение видимости токена"""
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")
    
    def _add_user_field(self):
        """Добавляет новое поле для User ID"""
        if len(self.user_id_vars) >= self.max_users:
            messagebox.showwarning("Предупреждение", f"Максимальное количество пользователей: {self.max_users}")
            return
        
        row = len(self.user_id_vars)
        
        # Создаем переменную для нового поля
        user_var = tk.StringVar()
        self.user_id_vars.append(user_var)
        
        # Создаем фрейм для поля и кнопки
        field_frame = ttk.Frame(self.users_frame)
        field_frame.pack(fill=tk.X, pady=2)
        
        # Поле ввода
        entry = ttk.Entry(field_frame, textvariable=user_var, width=50)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_id_entries.append(entry)
        
        # Кнопка удаления (показываем только если полей больше одного)
        remove_btn = ttk.Button(field_frame, text="➖", width=3, 
                               command=lambda idx=row: self._remove_user_field(idx))
        remove_btn.pack(side=tk.RIGHT, padx=(5, 0))
        self.remove_buttons.append(remove_btn)
        
        # Обновляем видимость кнопок удаления
        self._update_remove_buttons_visibility()
        
        # Обновляем состояние кнопки добавления
        if len(self.user_id_vars) >= self.max_users:
            self.add_user_btn.config(state='disabled')
    
    def _remove_user_field(self, index):
        """Удаляет поле User ID по индексу"""
        if len(self.user_id_vars) <= 1:
            messagebox.showwarning("Предупреждение", "Должен остаться хотя бы один пользователь")
            return
        
        # Удаляем элементы из списков
        self.user_id_vars.pop(index)
        entry = self.user_id_entries.pop(index)
        button = self.remove_buttons.pop(index)
        
        # Удаляем виджеты
        entry.master.destroy()
        
        # Пересоздаем все поля с правильными индексами
        self._recreate_user_fields()
        
        # Обновляем состояние кнопки добавления
        self.add_user_btn.config(state='normal')
    
    def _recreate_user_fields(self):
        """Пересоздает все поля пользователей с правильными индексами"""
        # Сохраняем текущие значения
        values = [var.get() for var in self.user_id_vars]
        
        # Очищаем контейнер
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        
        # Очищаем списки
        self.user_id_entries.clear()
        self.remove_buttons.clear()
        
        # Пересоздаем поля
        for i, value in enumerate(values):
            field_frame = ttk.Frame(self.users_frame)
            field_frame.pack(fill=tk.X, pady=2)
            
            # Поле ввода
            entry = ttk.Entry(field_frame, textvariable=self.user_id_vars[i], width=50)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.user_id_entries.append(entry)
            
            # Кнопка удаления
            remove_btn = ttk.Button(field_frame, text="➖", width=3, 
                                   command=lambda idx=i: self._remove_user_field(idx))
            remove_btn.pack(side=tk.RIGHT, padx=(5, 0))
            self.remove_buttons.append(remove_btn)
        
        # Обновляем видимость кнопок удаления
        self._update_remove_buttons_visibility()
    
    def _update_remove_buttons_visibility(self):
        """Обновляет видимость кнопок удаления"""
        show_buttons = len(self.user_id_vars) > 1
        for button in self.remove_buttons:
            if show_buttons:
                button.config(state='normal')
            else:
                button.config(state='disabled')
    
    def _get_config_path(self):
        """Получение пути к файлу конфигурации"""
        # Используем тот же метод, что и в config_loader
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent / "config-main.txt"
        else:
            return Path(__file__).parent.parent.parent / "config-main.txt"
    
    def _save_config(self):
        """Сохранение конфигурации"""
        try:
            bot_token = self.bot_token_var.get().strip()
            
            # Собираем все User ID
            user_ids = []
            for var in self.user_id_vars:
                user_id = var.get().strip()
                if user_id:  # Добавляем только непустые ID
                    user_ids.append(user_id)
            
            if not bot_token:
                messagebox.showwarning("Предупреждение", "Введите токен бота")
                return
            
            if not user_ids:
                messagebox.showwarning("Предупреждение", "Добавьте хотя бы один User ID")
                return
            
            # Проверяем уникальность User ID
            if len(user_ids) != len(set(user_ids)):
                messagebox.showwarning("Предупреждение", "User ID должны быть уникальными")
                return
            
            # Используем config_loader для сохранения
            config_data = {
                "BOT_TOKEN": bot_token,
                "ADMIN_ID": user_ids[0]  # Первый ID становится главным админом
            }
            
            # Если есть дополнительные ID, сохраняем их как дополнительные админы
            if len(user_ids) > 1:
                config_data["ADDITIONAL_ADMINS"] = ",".join(user_ids[1:])
            
            config_loader.save_config_txt(config_data)
            
            messagebox.showinfo("Успех", f"Настройки сохранены для {len(user_ids)} пользователей!")
            logger.info(f"Настройки сохранены через config_loader")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {e}")
    
    def _load_config(self):
        """Загрузка существующей конфигурации"""
        try:
            logger.info("Загрузка конфигурации через config_loader")
            
            # Перезагружаем конфигурацию
            config_loader.reload()
            
            # Заполняем токен
            bot_token = config_loader.get("BOT_TOKEN", "")
            self.bot_token_var.set(bot_token)
            
            # Загружаем User IDs
            admin_id = config_loader.get("ADMIN_ID", "")
            additional_admins = config_loader.get("ADDITIONAL_ADMINS", "")
            
            user_ids = []
            if admin_id:
                user_ids.append(admin_id)
            if additional_admins:
                user_ids.extend([uid.strip() for uid in additional_admins.split(',') if uid.strip()])
            
            # Очищаем существующие поля
            for widget in self.users_frame.winfo_children():
                widget.destroy()
            self.user_id_vars.clear()
            self.user_id_entries.clear()
            self.remove_buttons.clear()
            
            # Создаем поля для каждого User ID
            for user_id in user_ids:
                if len(self.user_id_vars) < self.max_users:
                    self._add_user_field()
                    self.user_id_vars[-1].set(user_id)
            
            # Если нет User ID, добавляем одно пустое поле
            if not user_ids:
                self._add_user_field()
            
            # Обновляем состояние кнопки добавления
            if len(self.user_id_vars) >= self.max_users:
                self.add_user_btn.config(state='disabled')
            else:
                self.add_user_btn.config(state='normal')
            
            if bot_token or user_ids:
                messagebox.showinfo("Успех", "Конфигурация загружена!")
            else:
                messagebox.showinfo("Информация", "Конфигурация пуста. Настройте параметры бота.")
            
            logger.info("Конфигурация загружена через config_loader")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить конфигурацию: {e}")
    
    def _clear_fields(self):
        """Очистка полей"""
        self.bot_token_var.set("")
        
        # Очищаем все User ID поля
        for var in self.user_id_vars:
            var.set("")
        
        logger.info("Поля конфигурации очищены")
    
    def get_config_data(self):
        """Получение данных конфигурации"""
        # Собираем все User ID из массива
        user_ids = []
        for var in self.user_id_vars:
            user_id = var.get().strip()
            if user_id:  # Добавляем только непустые ID
                user_ids.append(user_id)
        
        return {
            'bot_token': self.bot_token_var.get().strip(),
            'user_ids': user_ids,  # Возвращаем массив ID
            'user_id': user_ids[0] if user_ids else ''  # Для обратной совместимости
        }