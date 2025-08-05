"""
Вкладка логов для Etsy Parser
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class LogsTab:
    """Вкладка логов"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.log_handler = None
        
        self.create_widgets()
        self.setup_logging()
        # Автоматически загружаем логи при создании
        self.frame.after(1000, self._refresh_logs)
        # Автообновление каждые 2 секунды для синхронизации с консолью
        self._start_auto_refresh()
    
    def create_widgets(self):
        """Создание виджетов вкладки"""
        self.frame = ttk.Frame(self.parent)
        
        # Заголовок
        title_label = ttk.Label(self.frame, text="📝 Логи работы Etsy Parser", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=10)
        
        # Кнопки управления логами
        log_buttons_frame = ttk.Frame(self.frame)
        log_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_buttons_frame, text="🗑️ Очистить логи", 
                  command=self._clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons_frame, text="💾 Сохранить логи", 
                  command=self._save_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_buttons_frame, text="🔄 Обновить", 
                  command=self._refresh_logs).pack(side=tk.LEFT, padx=5)
        

        
        # Текстовое поле для логов
        self.log_text = scrolledtext.ScrolledText(
            self.frame, 
            wrap=tk.WORD, 
            font=('Consolas', 10), 
            bg='#1e1e1e', 
            fg='#ffffff',
            insertbackground='white',
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Настройка цветов для разных уровней логов
        self.log_text.tag_config("INFO", foreground="#00ff00")
        self.log_text.tag_config("WARNING", foreground="#ffff00")
        self.log_text.tag_config("ERROR", foreground="#ff0000")
        self.log_text.tag_config("DEBUG", foreground="#00ffff")
        self.log_text.tag_config("CRITICAL", foreground="#ff00ff")
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def setup_logging(self):
        """Настройка обработчика логов для GUI"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget, parent_tab):
                super().__init__()
                self.text_widget = text_widget
                self.parent_tab = parent_tab
            
            def emit(self, record):
                try:
                    msg = self.format(record)
                    level_name = record.levelname
                    
                    # Обновляем GUI в главном потоке
                    self.text_widget.after(0, self._update_text, msg, level_name)
                    
                except Exception:
                    pass
            
            def _update_text(self, msg, level_name):
                try:
                    self.text_widget.config(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, msg + '\n', level_name)
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state=tk.DISABLED)
                except Exception:
                    pass
        
        if self.log_text:
            self.log_handler = GUILogHandler(self.log_text, self)
            self.log_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.log_handler.setFormatter(formatter)
            
            # Добавляем обработчик к корневому логгеру
            logging.getLogger().addHandler(self.log_handler)
    

    
    def _clear_logs(self):
        """Очистка логов"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            logger.info("Логи очищены")
    
    def _save_logs(self):
        """Сохранение логов в файл"""
        try:
            if not self.log_text:
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialname=f"etsy_parser_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filename:
                logs_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(logs_content)
                
                messagebox.showinfo("Успех", f"Логи сохранены в {filename}")
                logger.info(f"Логи сохранены в файл: {filename}")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения логов: {e}")
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {e}")
    
    def _refresh_logs(self):
        """Обновление логов из файла"""
        try:
            log_file = 'logs/app.log'
            if not os.path.exists(log_file):
                return
            
            # Очищаем текущие логи
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            
            # Читаем последние 1000 строк из файла
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-1000:] if len(lines) > 1000 else lines
                
                for line in last_lines:
                    # Определяем уровень лога
                    level = "INFO"
                    if " - ERROR - " in line:
                        level = "ERROR"
                    elif " - WARNING - " in line:
                        level = "WARNING"
                    elif " - DEBUG - " in line:
                        level = "DEBUG"
                    elif " - CRITICAL - " in line:
                        level = "CRITICAL"
                    
                    self.log_text.insert(tk.END, line, level)
            
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Ошибка обновления логов: {e}")
    
    def _start_auto_refresh(self):
        """Запуск автообновления логов"""
        def auto_refresh():
            try:
                self._refresh_logs()
            except Exception:
                pass
            # Планируем следующее обновление
            if hasattr(self, 'frame') and self.frame.winfo_exists():
                self.frame.after(2000, auto_refresh)
        
        # Запускаем первое обновление
        self.frame.after(2000, auto_refresh)
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.log_handler:
            logging.getLogger().removeHandler(self.log_handler)