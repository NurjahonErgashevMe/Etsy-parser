"""
Точка входа для разового запуска парсинга Etsy магазинов
"""
from core.monitor import EtsyMonitor

def main():
    """Главная функция для разового парсинга"""
    print("🚀 Etsy Monitor - Разовый парсинг")
    print("=" * 50)
    
    # Создаём экземпляр монитора
    monitor = EtsyMonitor()
    
    # Запускаем один цикл мониторинга
    try:
        monitor.run_monitoring_cycle()
        print("\n🎉 Парсинг успешно завершён!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Парсинг прерван пользователем")
        
    except Exception as e:
        print(f"\n❌ Ошибка при парсинге: {e}")
        
    finally:
        print("👋 До свидания!")

if __name__ == "__main__":
    main()