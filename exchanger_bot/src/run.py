import asyncio
import threading
import time

# Импортируем функции запуска из обоих файлов
from client_bot import main as run_user_bot
from admin_bot import main as run_admin_bot

def run_bot_async(bot_func, name):
    """Запускает бота в отдельном потоке с собственным event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print(f"🚀 Запуск {name}...")
    try:
        bot_func()
    except Exception as e:
        print(f"❌ Ошибка в {name}: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 ОРКЕСТРАТОР БОТОВ")
    print("=" * 50)
    
    # Создаём потоки для каждого бота
    user_thread = threading.Thread(
        target=run_bot_async, 
        args=(run_user_bot, "USER BOT"),
        daemon=True
    )
    
    admin_thread = threading.Thread(
        target=run_bot_async, 
        args=(run_admin_bot, "ADMIN BOT"),
        daemon=True
    )
    
    # Запускаем потоки
    user_thread.start()
    admin_thread.start()
    
    print("✅ Оба бота запущены!")
    print("📌 Для остановки нажмите Ctrl+C\n")
    
    try:
        # Бесконечное ожидание
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка ботов...")